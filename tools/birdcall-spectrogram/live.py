#!/usr/bin/env python3
"""
live.py -- real-time scrolling spectrogram window for the birdsong lab.

Plug the audio in, run it, and watch. When you hear the call you like:
press F to freeze the picture, then S to save it.

    python3 live.py                      # system default input
    python3 live.py --device "USB"       # pick an input by name substring
    python3 live.py --list               # show input devices and exit

Keys (with the plot window focused)
-----------------------------------
  S          save PNG + WAV of what's on screen  ->  captures/live_<timestamp>.*
  F / space  freeze / unfreeze the display
  T          arm auto-trigger: the next loud burst freezes and saves by itself
  [ / ]      lower / raise the top of the frequency axis
  , / .      widen / narrow the time window on screen
  - / =      raise / lower the dB floor (contrast)
  W          toggle the waveform panel
  Q          quit

Why freeze matters: a swoop is ~130 ms wide and scrolls past in under a
second. Freeze (or arm the trigger) is what lets you actually catch it.
"""

import argparse
import os
import queue
import sys
import time
from datetime import datetime

import numpy as np
from scipy import signal
from scipy.io import wavfile

import matplotlib
for _backend in ("macosx", "TkAgg"):          # native window first, Tk fallback
    try:
        matplotlib.use(_backend, force=True)
        break
    except Exception:
        continue
import matplotlib.pyplot as plt


HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURES = os.path.join(HERE, "captures")

FMAX_STEPS = [1000, 2000, 3000, 4000, 6000, 8000, 12000, 16000, 24000]


class LiveSpectrogram:
    """Scrolling STFT display fed by a PortAudio input stream.

    Two ring buffers are kept in step:
      * `audio`  -- raw samples, so a save can write a real WAV
      * `img`    -- one column of dB magnitude per STFT hop, what you see

    Columns are computed incrementally (only for samples that just arrived)
    rather than re-running the whole spectrogram every frame, which keeps the
    redraw cheap enough to hold 25 fps.
    """

    def __init__(self, sd, device, sr, seconds, nperseg, hop, fmax, fmin,
                 db_floor, cmap, trigger_db, post_roll,
                 figsize=(11, 6.4), interval=66):
        self.sd = sd
        self.device = device
        self.sr = sr
        self.seconds = seconds
        self.nperseg = nperseg
        self.hop = hop
        self.fmin = fmin
        self.db_floor = db_floor
        self.trigger_db = trigger_db
        self.post_roll = post_roll
        self.figsize = figsize
        self.interval = interval

        self.window = signal.get_window("hann", nperseg)
        self.freqs = np.fft.rfftfreq(nperseg, 1.0 / sr)
        self.fmax_idx = min(range(len(FMAX_STEPS)),
                            key=lambda i: abs(FMAX_STEPS[i] - fmax))

        self.ncols = int(seconds * sr / hop)
        self.nrows = len(self.freqs)
        # dB magnitude image, newest column on the right
        self.img = np.full((self.nrows, self.ncols), -200.0)
        self.audio = np.zeros(int(seconds * sr))
        self.carry = np.zeros(0)

        self.q = queue.Queue()
        self.peak_db = -120.0
        self.frozen = False
        self.armed = False
        self.trigger_t = None
        self.show_wave = True
        self.flash = ("", 0.0)
        self.snapshot = None          # (img, audio) held while frozen
        self.dev_name = "?"           # filled in by run()

        # Reference level for the dB scale: full-scale sine through this
        # window. Fixed (not per-frame max) so the colors don't breathe as
        # the input level changes -- you can compare two frozen frames.
        self.ref = np.sum(self.window) / 2.0

        self.cmap = cmap
        self._build_figure()

    # ---------------------------------------------------------------- audio
    def _callback(self, indata, frames, time_info, status):
        if status:                                  # overflow etc.
            pass                                    # dropping a block is fine
        self.q.put(indata[:, 0].copy())

    def _drain(self):
        """Pull everything the audio thread queued since the last frame."""
        blocks = []
        while True:
            try:
                blocks.append(self.q.get_nowait())
            except queue.Empty:
                break
        if not blocks:
            return None
        return np.concatenate(blocks).astype(np.float64)

    def _push_columns(self, new):
        """Append new samples; emit one STFT column per hop that fits."""
        self.carry = np.concatenate([self.carry, new])
        cols = []
        while len(self.carry) >= self.nperseg:
            seg = self.carry[:self.nperseg]
            seg = seg - seg.mean()                  # per-frame DC removal
            spec = np.abs(np.fft.rfft(seg * self.window))
            cols.append(20.0 * np.log10(spec / self.ref + 1e-12))
            self.carry = self.carry[self.hop:]
        if cols:
            block = np.stack(cols, axis=1)
            k = block.shape[1]
            if k >= self.ncols:
                self.img = block[:, -self.ncols:]
            else:
                self.img = np.concatenate([self.img[:, k:], block], axis=1)

        n = len(new)                                # keep raw audio in step
        if n >= len(self.audio):
            self.audio = new[-len(self.audio):]
        elif n:
            self.audio = np.concatenate([self.audio[n:], new])

    # --------------------------------------------------------------- figure
    def _build_figure(self):
        self.fig = plt.figure(figsize=self.figsize)
        self.fig.canvas.manager.set_window_title("Live spectrogram")
        gs = self.fig.add_gridspec(2, 1, height_ratios=[1, 3.2], hspace=0.06,
                                   left=0.07, right=0.98, top=0.90, bottom=0.08)
        self.ax_w = self.fig.add_subplot(gs[0])
        self.ax_s = self.fig.add_subplot(gs[1], sharex=self.ax_w)

        t0 = -self.seconds
        self.line, = self.ax_w.plot(np.linspace(t0, 0, 2000),
                                    np.zeros(2000), lw=0.5, color="#1f4e79")
        self.ax_w.set_ylim(-1.05, 1.05)
        self.ax_w.set_ylabel("amplitude")
        self.ax_w.grid(alpha=0.25)
        self.ax_w.tick_params(labelbottom=False)
        self.ax_w.axhline(1.0, color="#d62728", lw=0.8, ls=":")
        self.ax_w.axhline(-1.0, color="#d62728", lw=0.8, ls=":")

        self.im = self.ax_s.imshow(
            self._visible_img(), aspect="auto", origin="lower",
            extent=[t0, 0, self.fmin, self._fmax()],
            vmin=self.db_floor, vmax=0, cmap=self.cmap,
            interpolation="bilinear")
        self.ax_s.set_xlabel("time (s, 0 = now)")
        self.ax_s.set_ylabel("frequency (Hz)")
        cb = self.fig.colorbar(self.im, ax=[self.ax_w, self.ax_s],
                               pad=0.012, aspect=34)
        cb.set_label("magnitude (dBFS)")

        # The status line is redrawn every frame, so it has to live inside an
        # axes -- only axes-level artists can be blitted.
        self.status = self.ax_s.text(
            0.006, 0.985, "", transform=self.ax_s.transAxes,
            va="top", ha="left", fontsize=9, family="monospace", color="#222",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#bbb",
                      alpha=0.85), animated=True)
        self.suptitle = self.fig.suptitle("", fontsize=10, y=0.975)
        self.hint = self.fig.text(
            0.5, 0.015,
            "S save   F/space freeze   T arm trigger   [ ] freq   , . time"
            "   - = contrast   W waveform   Q quit",
            ha="center", fontsize=8, color="#555")
        self.im.set_animated(True)
        self.line.set_animated(True)

        self.bg = None          # cached background for blitting; None = restale
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("resize_event", lambda e: self._invalidate())

    def _fmax(self):
        return min(FMAX_STEPS[self.fmax_idx], self.sr / 2)

    def _visible_img(self, img=None):
        """Rows of the image actually drawn: fmin..fmax.

        The bottom crop is not cosmetic vanity -- a windowed tone always leaks
        a little into the DC bin (~-40 dB for a Hann window), which otherwise
        paints a bright stripe along f=0 every time the call sounds.
        """
        img = self.img if img is None else img
        keep = (self.freqs >= self.fmin) & (self.freqs <= self._fmax())
        return img[keep]

    # ----------------------------------------------------------------- keys
    def _on_key(self, event):
        k = (event.key or "").lower()
        if k in ("f", " "):
            self.set_frozen(not self.frozen)
        elif k == "s":
            self.save()
        elif k == "t":
            self.armed = not self.armed
            self.trigger_t = None
            if self.armed:
                self.set_frozen(False)
            self._flash("trigger ARMED" if self.armed else "trigger off")
        elif k == "]":
            self.fmax_idx = min(self.fmax_idx + 1, len(FMAX_STEPS) - 1)
            self._rescale_y()
        elif k == "[":
            self.fmax_idx = max(self.fmax_idx - 1, 0)
            self._rescale_y()
        elif k in ("=", "+"):
            self.db_floor = min(self.db_floor + 5, -20)
            self.im.set_clim(self.db_floor, 0)
            self._invalidate()          # the colorbar behind us changed too
        elif k == "-":
            self.db_floor = max(self.db_floor - 5, -120)
            self.im.set_clim(self.db_floor, 0)
            self._invalidate()
        elif k in (",", "<"):
            self._resize_time(self.seconds * 1.5)
        elif k in (".", ">"):
            self._resize_time(self.seconds / 1.5)
        elif k == "w":
            self.show_wave = not self.show_wave
            self.ax_w.set_visible(self.show_wave)
            self._invalidate()

    def _resize_time(self, seconds):
        """Change how many seconds are on screen, keeping the newest data.

        Both ring buffers are re-cut; growing pads the left (older) end with
        silence, shrinking drops it. The display then simply has a new extent.
        """
        seconds = float(np.clip(seconds, 0.5, 30.0))
        ncols = max(20, int(seconds * self.sr / self.hop))
        nsamp = max(self.nperseg, int(seconds * self.sr))

        if ncols <= self.ncols:
            self.img = self.img[:, -ncols:]
        else:
            pad = np.full((self.nrows, ncols - self.ncols), -200.0)
            self.img = np.concatenate([pad, self.img], axis=1)
        if nsamp <= len(self.audio):
            self.audio = self.audio[-nsamp:]
        else:
            self.audio = np.concatenate([np.zeros(nsamp - len(self.audio)),
                                         self.audio])

        self.seconds, self.ncols = seconds, ncols
        self.snapshot = None
        self.frozen = False
        self.line.set_xdata(np.linspace(-seconds, 0, 2000))
        self.ax_w.set_xlim(-seconds, 0)
        self.suptitle.set_text(self._suptitle_text())
        self._rescale_y()
        self._flash(f"window {seconds:.1f} s")

    def _rescale_y(self):
        self.im.set_extent([-self.seconds, 0, self.fmin, self._fmax()])
        self.ax_s.set_ylim(self.fmin, self._fmax())
        self._invalidate()

    def _flash(self, msg, secs=2.5):
        self.flash = (msg, time.time() + secs)

    def set_frozen(self, val):
        if val and not self.frozen:
            self.snapshot = (self.img.copy(), self.audio.copy())
        self.frozen = val
        if not val:
            self.snapshot = None

    # ----------------------------------------------------------------- save
    def save(self):
        os.makedirs(CAPTURES, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(CAPTURES, f"live_{stamp}")
        n = 2                                  # two saves in one second
        while os.path.exists(base + ".png"):   # must not clobber each other
            base = os.path.join(CAPTURES, f"live_{stamp}_{n}")
            n += 1
        stamp = os.path.basename(base)[len("live_"):]

        audio = self.snapshot[1] if self.snapshot else self.audio
        wavfile.write(base + ".wav", self.sr,
                      (np.clip(audio, -1, 1) * 32767).astype(np.int16))

        # Hide the transient UI text so it doesn't end up in the saved figure.
        hint_vis = self.hint.get_visible()
        self.hint.set_visible(False)
        self.status.set_visible(False)
        for a in (self.im, self.line):      # animated artists are skipped by
            a.set_animated(False)           # savefig unless we un-flag them
        self.suptitle.set_text(
            f"live capture {stamp}   -   {self.sr/1000:g} kHz, "
            f"Hann {self.nperseg} ({self.nperseg/self.sr*1000:.0f} ms), "
            f"hop {self.hop/self.sr*1000:.1f} ms")
        self.fig.savefig(base + ".png", dpi=160)
        for a in (self.im, self.line):
            a.set_animated(True)
        self.status.set_visible(True)
        self.hint.set_visible(hint_vis)
        self.suptitle.set_text(self._suptitle_text())
        self._invalidate()

        print(f"saved {base}.png  and  {base}.wav")
        self._flash(f"saved {os.path.basename(base)}.png + .wav", 3.5)
        return base

    # ---------------------------------------------------------------- frame
    def _invalidate(self):
        """Force a full redraw + fresh background on the next tick.

        Needed whenever anything *behind* the blitted artists changes: axis
        limits, window size, a saved figure that rewrote the title.
        """
        self.bg = None

    def _suptitle_text(self):
        return (f"{self.dev_name}   -   {self.sr/1000:g} kHz, Hann "
                f"{self.nperseg} ({self.nperseg/self.sr*1000:.0f} ms), "
                f"{self.seconds:g} s window")

    def _tick(self):
        """Timer callback: pull audio, update artists, blit.

        Blitting is what makes this affordable. A full figure redraw costs
        ~55 ms here (axes, ticks, colorbar, and the image resample); restoring
        a cached background and redrawing only the image, the waveform and the
        status text costs ~20 ms, which fits comfortably in the 50 ms tick.
        """
        changed = self._compute()
        canvas = self.fig.canvas

        if self.bg is None:                  # first frame, or something behind
            canvas.draw()                    # the artists changed
            self.bg = canvas.copy_from_bbox(self.fig.bbox)
        elif self.frozen and not changed:
            return                           # nothing moving: don't burn CPU

        canvas.restore_region(self.bg)
        if self.show_wave:
            self.ax_w.draw_artist(self.line)
        self.ax_s.draw_artist(self.im)
        self.ax_s.draw_artist(self.status)
        canvas.blit(self.fig.bbox)

    def _compute(self):
        new = self._drain()
        if new is not None and new.size:
            self.peak_db = 20 * np.log10(np.max(np.abs(new)) + 1e-12)
            if not self.frozen:
                self._push_columns(new)
            # auto-trigger: fire on a loud block, save after the post-roll so
            # the whole call has scrolled into view
            if self.armed and self.trigger_t is None and \
                    self.peak_db > self.trigger_db:
                self.trigger_t = time.time()
                self._flash("triggered...", 1.0)
            if self.trigger_t and time.time() - self.trigger_t >= self.post_roll:
                self.set_frozen(True)
                self.save()
                self.armed = False
                self.trigger_t = None

        img = self.snapshot[0] if self.snapshot else self.img
        audio = self.snapshot[1] if self.snapshot else self.audio
        self.im.set_data(self._visible_img(img))

        if self.show_wave:
            step = max(1, len(audio) // 2000)
            y = audio[::step][:2000]
            if len(y) < 2000:
                y = np.pad(y, (2000 - len(y), 0))
            self.line.set_ydata(y)

        bits = [f"in: {self.dev_name}", f"peak {self.peak_db:6.1f} dBFS"]
        if self.peak_db > -0.5:
            bits.append("CLIPPING")
        if self.frozen:
            bits.append("FROZEN  (F to resume, S to save)")
        if self.armed:
            bits.append(f"ARMED  (>{self.trigger_db:.0f} dBFS)")
        msg, until = self.flash
        if msg and time.time() < until:
            bits.append(msg)
        text = "   |   ".join(bits)
        changed = text != self.status.get_text()
        self.status.set_text(text)
        self.status.set_color("#b00020" if (self.peak_db > -0.5 or self.frozen)
                              else "#222")
        return changed or not self.frozen

    # ----------------------------------------------------------------- main
    def run(self):
        sd = self.sd
        info = sd.query_devices(self.device if self.device is not None
                                else sd.default.device[0])
        self.dev_name = info["name"]
        print(f"listening on: {self.dev_name}   ({self.sr} Hz)")
        print("S save | F freeze | T arm trigger | [ ] freq | - = contrast | Q quit")

        stream = sd.InputStream(device=self.device, channels=1,
                                samplerate=self.sr, dtype="float32",
                                blocksize=self.hop * 2,
                                callback=self._callback)
        self.suptitle.set_text(self._suptitle_text())
        self.timer = self.fig.canvas.new_timer(interval=self.interval)
        self.timer.add_callback(self._tick)
        self.timer.start()
        with stream:
            plt.show()
        self.timer.stop()


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--device", help="input device index or name substring")
    p.add_argument("--list", action="store_true", help="list inputs and exit")
    p.add_argument("--rate", type=int, default=48000)
    p.add_argument("--seconds", type=float, default=6.0,
                   help="width of the scrolling window (default 6 s)")
    p.add_argument("--nperseg", type=int, default=1024,
                   help="FFT window length (512 = crisper timing, "
                        "2048 = finer frequency)")
    p.add_argument("--hop", type=int, default=256, help="samples between columns")
    p.add_argument("--fmax", type=float, default=8000, help="initial top of axis")
    p.add_argument("--fmin", type=float, default=50, help="bottom of axis, Hz")
    p.add_argument("--db-floor", dest="db_floor", type=float, default=-80)
    p.add_argument("--cmap", default="magma")
    p.add_argument("--trigger-db", dest="trigger_db", type=float, default=-25,
                   help="auto-trigger threshold in dBFS (T key)")
    p.add_argument("--post-roll", dest="post_roll", type=float, default=1.5,
                   help="seconds to keep recording after a trigger")
    p.add_argument("--fps", type=float, default=15,
                   help="display refresh rate (lower = less CPU)")
    p.add_argument("--figsize", default="11x6.4",
                   help="window size in inches, e.g. 13x7.5")
    args = p.parse_args()

    try:
        import sounddevice as sd
    except Exception as e:
        sys.exit(f"sounddevice unavailable ({e}). "
                 f"Install: python3 -m pip install --user sounddevice")

    if args.list:
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                print(f"{i:>3}  {d['name']}  "
                      f"({d['max_input_channels']} ch, "
                      f"{int(d['default_samplerate'])} Hz)")
        return

    device = None
    if args.device:
        if str(args.device).isdigit():
            device = int(args.device)
        else:
            m = [i for i, d in enumerate(sd.query_devices())
                 if args.device.lower() in d["name"].lower()
                 and d["max_input_channels"] > 0]
            if not m:
                sys.exit(f"no input matching {args.device!r}; try --list")
            device = m[0]

    app = LiveSpectrogram(sd, device, args.rate, args.seconds, args.nperseg,
                          args.hop, args.fmax, args.fmin, args.db_floor,
                          args.cmap, args.trigger_db, args.post_roll,
                          figsize=tuple(float(v) for v in
                                        args.figsize.lower().split("x")),
                          interval=max(20, int(1000 / max(args.fps, 1))))
    app.run()


if __name__ == "__main__":
    main()
