# Birdcall capture + spectrogram (ECE 4760 lab writeup)

```
MCU DAC --(audio)--> laptop input --> live scrolling spectrogram --> saved PNG + WAV
```

Two scripts:

| | |
|---|---|
| **`live.py`** | **Plug in, run, watch.** Real-time scrolling spectrogram window. Freeze the picture and hit **S** to save a PNG + WAV. This is the one you want at the bench. |
| `birdsong.py` | Offline tools: device list, level meter, fixed-length record, and a higher-quality re-render of any saved WAV. Use it after the fact to make the figure that actually goes in the report. |

Everything is installed for the system `python3` (`numpy`, `scipy`, `matplotlib`,
`sounddevice`). No venv, no activate step.

---

## Live view

Double-click **`Live Spectrogram.command`** in Finder, or:

```bash
cd ~/Developer/One_Off_Projects/birdcall-spectrogram
python3 live.py
```

It listens on whatever macOS has set as the current input, which is the
device that was most recently plugged in — so "plug it in and go" generally
just works. To force one: `python3 live.py --list` then
`python3 live.py --device "USB"` (index or name substring).

### Keys (plot window focused)

| Key | |
|---|---|
| **S** | Save PNG **and** WAV of what's on screen → `captures/live_<timestamp>.*` |
| **F** or space | Freeze / unfreeze |
| **T** | Arm auto-trigger — the next loud burst freezes and saves by itself |
| `[` `]` | Lower / raise the top of the frequency axis |
| `,` `.` | Widen / narrow the time window (0.5 s … 30 s) |
| `-` `=` | Raise / lower the dB floor (contrast) |
| **W** | Toggle the waveform panel |
| **Q** | Quit |

**Freeze is the important one.** A swoop is ~130 ms wide and scrolls off the
screen in under a second — you can't read it live. Workflow that works:

1. Play the call a few times, watch the peak-dBFS readout in the title, and
   set your volume so peaks land around **−12 to −6 dBFS**. The title turns
   red and says `CLIPPING` if you're too hot.
2. Press **T** to arm. Trigger the call. It freezes 1.5 s later and saves
   automatically — no reflexes required.
3. Or just press **F** right after the call and then **S**.
4. Press `.` a couple of times first if you want the call to fill more of the
   width; `[` to bring the top of the axis down to ~4 kHz for a swoop.

The saved WAV is the same audio as the picture, so you can always re-render it
later with different windowing:

```bash
python3 birdsong.py spec captures/live_20260911_154701.wav --trim --track --fmax 4000
```

That prints measured numbers you can quote — start/end frequency and duration —
and produces a tighter, higher-DPI figure than a screen grab.

### Useful flags

```bash
python3 live.py --seconds 3         # narrower time window at startup
python3 live.py --nperseg 512       # crisper timing, coarser frequency
python3 live.py --fmax 4000         # swoop-sized frequency axis
python3 live.py --trigger-db -35    # more sensitive auto-trigger
```

---

## Getting the sound into the laptop

Three options, easiest first. The handout says "any way you like," so pick
whichever works and say which one you used in the writeup.

**A. Acoustic — speaker to built-in mic (recommended, zero hardware fuss).**
Drive the lab speaker from the DAC as usual, put the laptop ~30 cm away in a
quiet room, run `live.py`. The built-in mic is flat enough to ~10 kHz for
this. It picks up room noise, which is fine — the call sits 40+ dB above it.
This is also exactly what the Merlin app does.

**B. Aux cable into a USB audio interface or the lab PC's line-in (cleanest).**
A real line input takes 0–3.3 V happily and gives a noise-free capture. Plug
it in, re-run `--list`, point `--device` at it.

**C. Aux cable straight into the MacBook's 3.5 mm jack (finicky — read this).**
The MacBook jack is a *headset* jack, not a line-in. Two things bite:

1. **Wiring.** A plain TRS aux cable will never enumerate as an input — the mic
   signal has to land on the 4th (TRRS) contact. You need a TRRS headset
   splitter and to feed the *microphone* branch. If no new input shows up in
   `python3 live.py --list` after plugging in, this is why.
2. **Level.** The mic input expects tens of millivolts; the DAC swings
   ~0–3.3 V, which clips hard and smears fake harmonics across the
   spectrogram. Attenuate roughly 30:1 first — a 33 kΩ / 1 kΩ divider, or a pot.

### macOS microphone permission

The first run triggers a permission prompt. If the display stays flat at
−120 dBFS, the app running the command was never granted access: **System
Settings → Privacy & Security → Microphone** → enable Terminal (or whichever
app you launched from), then restart that app.

---

## `birdsong.py` (offline)

| Command | What it does |
|---|---|
| `devices` | Lists every input/output with its index. Plug the cable in *first*. |
| `level --device X` | Text peak/RMS meter, if you'd rather not open the GUI. |
| `record out.wav -d 5` | Countdown, then a fixed-length take. `--spec` renders the figure right after. |
| `spec in.wav` | Waveform + spectrogram PNG, plus printed measurements. |
| `synth out.wav` | Writes a synthetic 1740→1100 Hz swoop — test the whole plotting path with no hardware. |

Flags on `spec` worth knowing:

| Flag | Default | Why you'd change it |
|---|---|---|
| `--trim` | off | Crops to the loudest burst, so a 130 ms call isn't lost in 6 s of silence. |
| `--track` | off | Overlays the peak-frequency ridge. Makes the sweep unmistakable. |
| `--fmax` | 8000 | Drop to `4000` for a swoop; raise for the chirp's upper harmonics. |
| `--nperseg` | 1024 | The core trade-off. 1024 @ 48 kHz = 21 ms window, 47 Hz bins. **Lower (256/512) for short fast chirps** where *when* matters; raise (2048) for a sustained tone where *what frequency* matters. |
| `--db-floor` | −70 | Raise toward −50 if the noise floor looks mushy; lower to show quiet harmonics. |
| `--hpf` | 60 | High-pass corner — kills mains hum and DC. `0` disables. |

---

## For the writeup

- **Scope display (rise / sustain / fall):** take that off the oscilloscope at
  the bench — the handout asks for a scope capture specifically. The waveform
  panel here shows the same envelope from the recorded audio and makes a good
  companion figure, but it isn't a substitute for the scope photo.
- **Spectrogram:** freeze, save, then re-render the WAV with `birdsong.py spec`
  for the final figure. Caption it with which capture path you used (A/B/C),
  the sample rate, and the window length — the figure subtitle prints all
  three.
- The printed `peak freq start → end` line lets you state the measured sweep
  and compare it to the frequencies your code was told to produce. Any gap is
  worth a sentence of discussion: window smearing, DAC update rate, speaker
  response.
- Keep the WAVs. If a figure gets questioned you can re-render it with
  different windowing in one command.
