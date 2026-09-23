# Lab 1 requirements, and where each one stands

Summarised from the Lab 1 handout and the course report policy (ECE 4760,
undergraduate track). Status
as of 2026-09-23: all three weekly checkoffs passed; the report is what's left.

---

## Checkpoints

### Week 1 — checked off

| Requirement | Where it is |
| --- | --- |
| Wire the MCP4822 DAC per the demo's `#define`s; build and load the DDS demo | notebook §3 wiring, §5 |
| Confirm the waveform on the scope; listen through a 3.5 mm socket | notebook §5 |
| Send the waveform to the other DAC channel | `DAC_config_chan_B` in `birdsong.c` |
| Add the bootsel/reset button | notebook §3, RUN pin 30 to GND |
| Add a slide pot; verify with the ADC demo | notebook §5, step 6 |
| Integrate ADC and DDS; pot sets 0 to ~10 kHz | `adc_to_phase_incr()`, `MAX_FREQ_HZ` |

### Week 2 — checked off

| Requirement | Where it is |
| --- | --- |
| Wire the keypad; verify with the keypad demo | notebook §6 |
| 0 key toggles the tone, debounced | `protothread_core_0`, four-state debounce |
| `*` → record mode; hold 1–9 records the frequency at ~100 Hz; release stops; press again plays back | `protothread_toggle25` (100 Hz capture), `protothread_playback` |
| GPIO set on ISR entry, cleared on exit; measure ISR time on the scope | `ISR_GPIO 2`; measurement still blank in notebook §6 |

### Week 3 (4760) — checked off, demo included

| Requirement | Where it is |
| --- | --- |
| Boots in tone-generator mode, pot sets pitch | `tone` starts `true` |
| 0 silences / restarts the tone generator | key 0 branch |
| `*` → record mode; hold 1–9 records while held; release stops | `record_mode`, release in `MAYBE_NOT_PRESSED` |
| Same key plays back at 8–10× speed | 10×: recorded every 10 ms, replayed every 1 ms |
| Different sounds on each key 1–9 | `recordings[10][2500]` |
| `#` → compose mode; keys pressed are recorded as a sequence | `sequence[]`, `compose_mode` |
| `#` again plays the sequence back | `playing_sequence` in the playback thread |
| ISR timing GPIO; measure on the scope | as week 2 |
| Demo: imitate Fig. 2, replay a TA's sequence, no reset or reprogramming | passed |

---

## Report

See `report-guide.md` for how the professor's example reports are laid out.

One report per group, submitted on Canvas. Written so that in two years you
could rebuild the project and understand the method from the report alone.

| # | Section | What it needs | What exists | Still to do |
| --- | --- | --- | --- | --- |
| 1 | Introduction | short account of what was done | — | write it |
| 2 | Design and testing methods | software and hardware approach; tests that convince a reader the requirements are met; **AI use** | notebook §3 system, §5–6 order of work, §7 method, §8 design decisions, §9 bug log | write it up from those; describe each test and its result |
| 3 | Documentation | drawings, flowcharts, schematics, program listing with comments | wiring table (notebook §3); wiring diagrams in `docs/ECE4760_birdsong-lab-field-guide.html` | **schematic**, **flowchart** of the threads/modes and debounce state machine, commented listing |
| 4 | Results | how fast, how accurate, error ranges | computed figures only (notebook §4) | **all measurements** — see below |
| 5 | Conclusions | usability, what you'd change, comments on the lab | — | write it |
| 6 | Answers to specific questions | lab-writeup questions | prep answers, notebook §10 | check they cover what the writeup asks |

### Required extras

| Item | Status |
| --- | --- |
| Scope display of a swoop/chirp showing rise, sustain, fall | **not captured** — method in notebook §12 |
| Spectrogram of the sound the MCU produced | **not captured** — use `tools/birdcall-spectrogram/` |
| Heavily commented code listing | `Lab1_Birdsong/birdsong.c` is commented; check no comment contradicts its line |
| AI prompt log: words exchanged, additions/deletions/modifications suggested and accepted | notebook §11 has commits, line counts, accepted/rejected and word counts |

### Measurements that Results needs

All are `___` in the notebook today.

- **Speed:** ISR pulse width and period on GPIO 2, with and without the
  envelope (`Lab1_Birdsong` vs `Lab1_Birdsong_NoEnvelope`); duty cycle.
- **Accuracy:** scope frequency against the intended frequency at several
  slider positions (bottom, middle, top); peak-to-peak amplitude; envelope rise
  and fall times against the designed 5 ms.
- **Timing:** playback duration against the expected duration. The serial
  output prints `played key N: S samples in T ms` for every single-key playback,
  which gives this directly (expected T = S ms).
- **Spectrogram:** measured start/end frequency of a swoop against what the
  code was told to produce (`birdsong.py spec --track` prints this).
