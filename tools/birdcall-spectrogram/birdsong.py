#!/usr/bin/env python3
"""
birdsong.py -- capture + spectrogram toolkit for the ECE 4760 birdsong lab.

Pipeline:  MCU DAC out --(aux cable)--> laptop audio input --> WAV --> spectrogram PNG

Subcommands
-----------
  devices                 list audio input/output devices (find your input!)
  level                   live peak/RMS meter -- use this to set volume before recording
  record  out.wav         record N seconds of audio to a WAV file
  spec    in.wav          render waveform + spectrogram figure to PNG
  synth   out.wav         generate a synthetic swoop/chirp WAV (test the pipeline
                          with no hardware attached)

Examples
--------
  python3 birdsong.py devices
  python3 birdsong.py level --device "External"
  python3 birdsong.py record captures/swoop.wav -d 5 --device "External"
  python3 birdsong.py spec captures/swoop.wav --fmax 6000 --trim --track
  python3 birdsong.py synth captures/fake.wav && python3 birdsong.py spec captures/fake.wav
"""

import argparse
import sys
import os

import numpy as np
from scipy.io import wavfile
from scipy import signal

import matplotlib
matplotlib.use("Agg")          # headless: write PNGs, never open a window
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def _sd():
    """Import sounddevice lazily so `spec`/`synth` work even without PortAudio."""
    try:
        import sounddevice as sd
        return sd
    except Exception as e:                                    # pragma: no cover
        sys.exit(f"sounddevice unavailable ({e}).\n"
                 f"Install with:  python3 -m pip install --user sounddevice")


def resolve_device(spec_str, want_input=True):
    """Accept a device index ('2') or a case-insensitive name substring."""
    if spec_str is None:
        return None
    sd = _sd()
    if str(spec_str).isdigit():
        return int(spec_str)
    key = "max_input_channels" if want_input else "max_output_channels"
    matches = [i for i, d in enumerate(sd.query_devices())
               if spec_str.lower() in d["name"].lower() and d[key] > 0]
    if not matches:
        sys.exit(f"No {'input' if want_input else 'output'} device matching "
                 f"{spec_str!r}. Run: python3 birdsong.py devices")
    return matches[0]


def load_wav(path):
    """Read a WAV as mono float64 in [-1, 1], DC offset removed.

    The DAC idles near mid-scale (~1.65 V), so the raw capture usually carries a
    large DC term. A coupling cap in the cable often removes it; subtracting the
    mean guarantees it either way, which keeps the spectrogram's 0 Hz bin from
    swamping the color scale.
    """
    sr, raw = wavfile.read(path)
    raw = np.asarray(raw)
    x = raw.astype(np.float64)
    if x.ndim > 1:                       # stereo -> mono (the jack usually
        x = x.mean(axis=1)               # duplicates the signal on both channels)
    if np.issubdtype(raw.dtype, np.integer):
        x /= float(np.iinfo(raw.dtype).max)     # ints -> +/-1.0
    x -= x.mean()                                # kill DC
    return sr, x


def save_wav(path, sr, x_float):
    """Write float audio as 16-bit PCM, warning if the capture clipped."""
    peak = float(np.max(np.abs(x_float))) if x_float.size else 0.0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    x_i16 = np.clip(x_float, -1.0, 1.0)
    wavfile.write(path, sr, (x_i16 * 32767).astype(np.int16))
    return peak


def moving_rms(x, win):
    """RMS envelope via a boxcar convolution -- used for auto-trimming."""
    p = np.convolve(x ** 2, np.ones(win) / win, mode="same")
    return np.sqrt(p)


def auto_trim(x, sr, drop_db=35.0, pad_s=0.05):
    """Crop to the loudest contiguous burst (the birdcall) plus a little padding.

    Keeps every sample whose short-time RMS is within `drop_db` of the loudest
    frame, then takes the first-to-last such sample. Good enough for a single
    isolated call, which is all we ever record here.
    """
    win = max(16, int(0.005 * sr))                 # 5 ms RMS window
    env = moving_rms(x, win)
    if env.max() <= 0:
        return x, 0.0
    thresh = env.max() * (10 ** (-drop_db / 20.0))
    idx = np.flatnonzero(env >= thresh)
    if idx.size == 0:
        return x, 0.0
    pad = int(pad_s * sr)
    i0 = max(0, idx[0] - pad)
    i1 = min(len(x), idx[-1] + pad)
    return x[i0:i1], i0 / sr


# ----------------------------------------------------------------------------
# subcommand: devices
# ----------------------------------------------------------------------------

def cmd_devices(args):
    sd = _sd()
    print(f"{'idx':>3}  {'in':>2} {'out':>3}  {'rate':>6}  name")
    print("-" * 60)
    for i, d in enumerate(sd.query_devices()):
        print(f"{i:>3}  {d['max_input_channels']:>2} {d['max_output_channels']:>3}"
              f"  {int(d['default_samplerate']):>6}  {d['name']}")
    print("\nDefault (input, output):", sd.default.device)
    print("\nPlug the aux cable in first -- the jack shows up as a NEW input\n"
          "device (often 'External Microphone'). If no new device appears, see\n"
          "the 'Mac headphone jack' note in README.md.")


# ----------------------------------------------------------------------------
# subcommand: level  (set your volume before you burn a take)
# ----------------------------------------------------------------------------

def cmd_level(args):
    sd = _sd()
    dev = resolve_device(args.device, want_input=True)
    sr = args.rate
    print("Play the call in a loop. Aim for peaks around -12 to -6 dBFS.")
    print("Ctrl-C to stop.\n")

    def cb(indata, frames, time_info, status):
        x = indata[:, 0].astype(np.float64)
        peak = np.max(np.abs(x)) + 1e-12
        rms = np.sqrt(np.mean(x ** 2)) + 1e-12
        pk_db, rms_db = 20 * np.log10(peak), 20 * np.log10(rms)
        bar = int(np.clip((pk_db + 60) / 60 * 40, 0, 40))      # -60..0 dBFS
        flag = "  <-- CLIPPING" if peak >= 0.999 else ""
        print(f"\rpeak {pk_db:7.1f} dBFS  rms {rms_db:7.1f}  "
              f"|{'#' * bar}{'.' * (40 - bar)}|{flag}", end="", flush=True)

    with sd.InputStream(device=dev, channels=1, samplerate=sr,
                        blocksize=int(sr * 0.05), callback=cb):
        try:
            while True:
                sd.sleep(200)
        except KeyboardInterrupt:
            print("\nstopped.")


# ----------------------------------------------------------------------------
# subcommand: record
# ----------------------------------------------------------------------------

def cmd_record(args):
    sd = _sd()
    dev = resolve_device(args.device, want_input=True)
    sr = args.rate
    n = int(args.duration * sr)

    name = sd.query_devices(dev)["name"] if dev is not None else "system default"
    print(f"Recording {args.duration:g} s @ {sr} Hz from: {name}")
    for k in range(args.countdown, 0, -1):
        print(f"  {k}...", flush=True)
        sd.sleep(1000)
    print("  GO -- trigger the call now.")

    rec = sd.rec(n, samplerate=sr, channels=1, dtype="float32", device=dev)
    sd.wait()
    x = rec[:, 0].astype(np.float64)

    peak = save_wav(args.out, sr, x)
    pk_db = 20 * np.log10(peak + 1e-12)
    print(f"Wrote {args.out}  ({len(x)/sr:.2f} s, peak {pk_db:.1f} dBFS)")
    if peak >= 0.999:
        print("  !! CLIPPED -- turn the source down and retake; clipping adds "
              "fake harmonics to the spectrogram.")
    elif pk_db < -30:
        print("  !! very quiet -- turn the source up or raise input gain in "
              "System Settings > Sound > Input.")

    if args.spec:                                   # render immediately
        args.wav = args.out
        args.png = None
        cmd_spec(args)


# ----------------------------------------------------------------------------
# subcommand: spec
# ----------------------------------------------------------------------------

def cmd_spec(args):
    sr, x = load_wav(args.wav)

    # High-pass away rumble: 60 Hz mains hum, cable/handling thumps, and the
    # residual DC step. Nothing in a birdcall lives down there, and leaving it
    # in costs contrast because the color scale is normalized to the peak bin.
    if args.hpf and args.hpf > 0:
        sos = signal.butter(4, args.hpf, btype="highpass", fs=sr, output="sos")
        x = signal.sosfiltfilt(sos, x)

    t_offset = 0.0
    if args.trim:
        x, t_offset = auto_trim(x, sr, drop_db=args.trim_db)
        if len(x) < 256:
            sys.exit("auto-trim found (almost) nothing -- drop --trim, or record again")

    # window/overlap: the trade-off that decides how the figure reads.
    #   big nperseg  -> fine frequency detail, smeared in time
    #   small nperseg-> crisp onsets, coarse frequency
    # 1024 @ 48 kHz = 21 ms window, ~47 Hz bins: reads a 2 s swoop nicely.
    nper = args.nperseg
    nover = int(nper * args.overlap)

    f, t, Sxx = signal.spectrogram(
        x, fs=sr,
        window="hann",
        nperseg=nper,
        noverlap=nover,
        nfft=nper * args.zeropad,        # zero-pad => smoother-looking ridge
        scaling="spectrum",
        mode="magnitude",
    )
    S_db = 20 * np.log10(Sxx + 1e-12)
    S_db -= S_db.max()                   # 0 dB == loudest bin in the take

    # Crop the frequency axis. The bottom crop matters: a windowed tone always
    # leaks a little into the DC bin (~-40 dB for a Hann window), which would
    # otherwise paint a bright stripe along f=0 and distract from the call.
    fmax = args.fmax if args.fmax else sr / 2
    keep = (f <= fmax) & (f >= args.fmin)
    f, S_db = f[keep], S_db[keep]

    tw = np.arange(len(x)) / sr          # waveform time axis

    # ---- figure ------------------------------------------------------------
    both = args.panels == "both"
    if both:
        fig, (ax0, ax1) = plt.subplots(
            2, 1, figsize=(args.width, args.height), sharex=True,
            gridspec_kw={"height_ratios": [1, 2.4], "hspace": 0.08})
    else:
        fig, ax1 = plt.subplots(figsize=(args.width, args.height * 0.72))
        ax0 = None

    if ax0 is not None:                  # scope-style waveform / envelope
        ax0.plot(tw, x, lw=0.5, color="#1f4e79")
        env = moving_rms(x, max(16, int(0.005 * sr)))
        ax0.plot(tw, env * np.sqrt(2), lw=1.2, color="#d62728",
                 label="RMS envelope")
        ax0.plot(tw, -env * np.sqrt(2), lw=1.2, color="#d62728")
        ax0.set_ylabel("amplitude")
        ax0.legend(loc="upper right", fontsize=8, framealpha=0.9)
        ax0.grid(alpha=0.25)
        ax0.margins(x=0)

    pcm = ax1.pcolormesh(t, f, S_db, shading="gouraud",
                         cmap=args.cmap, vmin=args.db_floor, vmax=0)
    ax1.set_ylabel("frequency (Hz)")
    ax1.set_xlabel("time (s)")
    ax1.margins(x=0)

    if args.track:
        # Per-frame peak-frequency ridge. Only drawn where the frame is loud
        # enough to be the call rather than the noise floor -- otherwise the
        # trace wanders randomly during silence.
        frame_db = S_db.max(axis=0)
        pk = f[np.argmax(S_db, axis=0)]
        pk = np.where(frame_db > args.db_floor + 12, pk, np.nan)
        ax1.plot(t, pk, color="w", lw=1.1, alpha=0.85)
        ax1.plot(t, pk, color="k", lw=0.5, alpha=0.6,
                 label="peak-frequency track")
        ax1.legend(loc="upper right", fontsize=8, framealpha=0.9)

    cb = fig.colorbar(pcm, ax=[a for a in (ax0, ax1) if a is not None],
                      pad=0.015, aspect=30)
    cb.set_label("magnitude (dB re. peak)")

    title = args.title or os.path.basename(args.wav)
    sub = (f"{sr/1000:g} kHz - Hann {nper} ({nper/sr*1000:.0f} ms), "
           f"{int(args.overlap*100)}% overlap, {f[1]-f[0]:.0f} Hz bins")
    if t_offset:
        sub += f" - trimmed from t={t_offset:.2f} s"
    (ax0 or ax1).set_title(f"{title}\n{sub}", fontsize=10)

    png = args.png or os.path.splitext(args.wav)[0] + "_spectrogram.png"
    fig.savefig(png, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {png}")

    # ---- numbers worth quoting in the writeup ------------------------------
    frame_db = S_db.max(axis=0)
    loud = frame_db > args.db_floor + 12
    if loud.any():
        pk = f[np.argmax(S_db, axis=0)][loud]
        tl = t[loud]
        print(f"  call spans  {tl[0]:.3f} -> {tl[-1]:.3f} s "
              f"({(tl[-1]-tl[0])*1000:.0f} ms)")
        print(f"  peak freq   start {pk[0]:.0f} Hz -> end {pk[-1]:.0f} Hz "
              f"(min {pk.min():.0f}, max {pk.max():.0f})")


# ----------------------------------------------------------------------------
# subcommand: synth  (pipeline test with no hardware)
# ----------------------------------------------------------------------------

def cmd_synth(args):
    """Fake a swoop: 1740 -> 1100 Hz over 130 ms, raised-cosine amplitude ramps.

    Matches the lab's swoop spec closely enough to sanity-check the plotting
    code before you're standing at the bench.
    """
    sr = args.rate
    dur = 0.130
    n = int(dur * sr)
    tt = np.arange(n) / sr

    f0, f1 = 1740.0, 1100.0
    phase = 2 * np.pi * (f0 * tt + 0.5 * (f1 - f0) / dur * tt ** 2)
    tone = np.sin(phase)

    # amplitude envelope: 10 ms rise, sustain, 10 ms fall (raised cosine)
    ramp = int(0.010 * sr)
    env = np.ones(n)
    env[:ramp] = 0.5 * (1 - np.cos(np.pi * np.arange(ramp) / ramp))
    env[-ramp:] = env[:ramp][::-1]
    call = 0.7 * tone * env

    pre, post = int(0.25 * sr), int(0.35 * sr)
    x = np.concatenate([np.zeros(pre), call, np.zeros(post)])
    x += args.noise * np.random.randn(len(x))            # a little hiss

    save_wav(args.out, sr, x)
    print(f"Wrote {args.out}  (synthetic swoop 1740->1100 Hz, 130 ms)")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    d = sp.add_parser("devices", help="list audio devices")
    d.set_defaults(func=cmd_devices)

    l = sp.add_parser("level", help="live input level meter")
    l.add_argument("--device", help="input device index or name substring")
    l.add_argument("--rate", type=int, default=48000)
    l.set_defaults(func=cmd_level)

    r = sp.add_parser("record", help="record to WAV")
    r.add_argument("out")
    r.add_argument("-d", "--duration", type=float, default=5.0, help="seconds")
    r.add_argument("--device", help="input device index or name substring")
    r.add_argument("--rate", type=int, default=48000)
    r.add_argument("--countdown", type=int, default=3)
    r.add_argument("--spec", action="store_true",
                   help="render the spectrogram right after recording")
    # `record --spec` reuses cmd_spec, so give it cmd_spec's defaults
    r.set_defaults(png=None, fmax=8000, nperseg=1024, overlap=0.875, zeropad=2,
                   fmin=50, db_floor=-70, cmap="magma", hpf=60,
                   trim=False, trim_db=35,
                   track=True, panels="both", title=None,
                   width=10, height=6.5, dpi=160)

    s = sp.add_parser("spec", help="render spectrogram PNG from a WAV")
    s.add_argument("wav")
    s.add_argument("--png", help="output path (default: <wav>_spectrogram.png)")
    s.add_argument("--fmax", type=float, default=8000,
                   help="top of frequency axis, Hz (default 8000; 0 = Nyquist)")
    s.add_argument("--fmin", type=float, default=50,
                   help="bottom of frequency axis, Hz (default 50)")
    s.add_argument("--nperseg", type=int, default=1024, help="FFT window length")
    s.add_argument("--overlap", type=float, default=0.875, help="0..0.95")
    s.add_argument("--zeropad", type=int, default=2, help="nfft = nperseg * this")
    s.add_argument("--db-floor", dest="db_floor", type=float, default=-70,
                   help="darkest dB shown (default -70)")
    s.add_argument("--cmap", default="magma")
    s.add_argument("--hpf", type=float, default=60,
                   help="high-pass corner in Hz before analysis (0 = off)")
    s.add_argument("--trim", action="store_true", help="crop to the loudest burst")
    s.add_argument("--trim-db", dest="trim_db", type=float, default=35)
    s.add_argument("--track", action="store_true",
                   help="overlay the peak-frequency ridge")
    s.add_argument("--panels", choices=["both", "spec"], default="both")
    s.add_argument("--title")
    s.add_argument("--width", type=float, default=10)
    s.add_argument("--height", type=float, default=6.5)
    s.add_argument("--dpi", type=int, default=160)

    y = sp.add_parser("synth", help="write a synthetic swoop WAV (no hardware)")
    y.add_argument("out")
    y.add_argument("--rate", type=int, default=48000)
    y.add_argument("--noise", type=float, default=0.002)
    y.set_defaults(func=cmd_synth)

    # record/spec need their func set after all args are declared
    r.set_defaults(func=cmd_record)
    s.set_defaults(func=cmd_spec)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
