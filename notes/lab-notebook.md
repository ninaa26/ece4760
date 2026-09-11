# Lab notebook — Lab 1, Synthesizing Birdsong

ECE 4760, Cornell, Fall 2025
Nina (ninaa26) · Raspberry Pi Pico 2 / RP2350
Repo: https://github.com/ninaa26/ece4760

Fields written as `___` still need a measurement taken at the bench. Do not
write a number here that was not read off an instrument.

---

## 1. System as built

### Hardware

| Pico | Connects to | Notes |
| --- | --- | --- |
| 3V3(OUT) pin 36 | + rail → DAC pin 1 (VDD) | |
| GND pin 38 | − rail → DAC pin 7 (VSS) and pin 5 (LDAC) | LDAC tied low: output updates immediately |
| GPIO 5 | DAC pin 2 (CS) | active low |
| GPIO 6 | DAC pin 3 (SCK) | |
| GPIO 7 | DAC pin 4 (SDI) | called MOSI on the Pico side |
| GPIO 2 | oscilloscope | ISR timing pin |
| GPIO 26 | potentiometer pin 2 (wiper) | ADC channel 0 |
| — | pot pins 1 and 3 → 3.3 V and GND | 1 and 3 are the track ends |
| GPIO 9–12 | keypad Row 1–4, each via 330 Ω | resistors are required |
| GPIO 13–15 | keypad Col 1–3 | direct, internal pull-ups enabled |
| DAC pin 6 (VOUTB) | scope probe and audio jack tip | jack sleeve to ground |
| pin 30 (RUN) ↔ pin 28 (GND) | reset push button | double-press enters bootloader |

Keypad header order on the lab's 3×4 units is
`Col1 Col2 Col3 Row1 Row2 Row3 Row4 NC`. The header comment in the course
`keypad.c` assumes a different part and lists rows first — wire by function.

### Software configuration

| Constant | Value | Meaning |
| --- | --- | --- |
| `set_sys_clock_khz` | 150 000 | 150 MHz system clock |
| `Fs` | 50 000 | audio samples per second |
| `DELAY` | 20 | µs between alarm interrupts (1/Fs) |
| `sine_table_size` | 256 | entries, indexed by the accumulator's top 8 bits |
| `MAX_FREQ_HZ` | 10 000.0 | top of the slider's range |
| `NUM_RECORD_KEYS` | 10 | slot 0 unused so index N = key N |
| `MAX_SAMPLES` | 1000 | 10 seconds per key at 100 Hz |
| SPI baud | 20 MHz | 16-bit frames, mode 0 |

Build: `text 27,348 · bss 24,508` of the RP2350's 520 KB.

### Concurrency structure

| Runs | Rate | Job |
| --- | --- | --- |
| `alarm_irq` (ISR) | 50 000 Hz | one audio sample: accumulate → sine table → DAC |
| `protothread_toggle25` | 100 Hz | read pot, set pitch, append to a recording |
| `protothread_playback` | 100 Hz | step a stored recording back out |
| `protothread_core_0` | 33 Hz | scan keypad, debounce, set modes |

Each stored pitch is held for 500 ISR ticks (50 000 / 100), which is why
sampling the slider at a lazy 100 Hz still produces continuous sound.

---

## 2. Week 1

**Checkpoint:** DAC wired and producing a tone, confirmed on the scope and
through an audio jack; output moved to the second DAC channel; reset button
added; potentiometer wired and verified with the ADC demo; ADC and DDS
integrated so the slider sets the frequency over 0 to ~10 kHz.

### Measurements

| Quantity | Value | Expected |
| --- | --- | --- |
| Output frequency, demo default | ___ Hz | 800 Hz |
| Output amplitude, peak to peak | ___ V | 0–2.048 V at gain 1× |
| Frequency, slider at bottom | ___ Hz | ~0 |
| Frequency, slider at top | ___ Hz | ~10 000 |
| ADC reading, slider at bottom | ___ | ~0 |
| ADC reading, slider at top | ___ | ~4095 |
| Scope settings used | ___ V/div, ___ µs/div | 0.5 V/div, 250 µs/div at 800 Hz |

### Observations

- 
- 

### Problems and how they were resolved

- 

---

## 3. Week 2

**Checkpoint:** keypad wired and verified; key 0 toggles the tone on a clean
debounced press; `*` enters record mode; holding a key 1–9 records the
frequency while held; pressing that key again plays the recording back; ISR
execution time measured on the scope.

### Measurements

| Quantity | Value | Expected |
| --- | --- | --- |
| ISR pulse width on GPIO 2 | ___ µs | small fraction of 20 µs |
| ISR period on GPIO 2 | ___ µs | 20.0 |
| ISR duty cycle | ___ % | width ÷ 20 µs |
| Pulse width before week 2 changes | ___ µs | baseline for comparison |
| Recording length, 2 s hold | ___ samples | ~200 at 100 Hz |
| Keys verified working | ___ | all twelve |

### Observations

- 
- 

### Problems and how they were resolved

See the bug log in section 5.

---

## 4. Design decisions

**Store the pitch, not the audio.** A recording is a list of frequencies
sampled at 100 Hz, not a waveform. Audio would be 50 000 numbers a second;
pitches are 100 — five hundred times less. It also means playback can be sped
up 8–10× in week 3 without the pitch rising, because speeding up a list of
pitches replays the same notes faster, where speeding up audio would raise
every frequency.

**Recording lives in the 100 Hz thread, not the keypad thread.** The lab asks
for ~100 Hz storage and the keypad thread runs at 33 Hz, so capturing there
would lose two thirds of the detail. The keypad thread sets flags; the ADC
thread does the capture.

**A mode gate on the pot read.** Both the ADC thread and the playback thread
write `phase_incr_main` at 100 Hz. Without `if (!playing)` around the pot read
they alternate and the slider overwrites roughly half the recorded samples.

**`uint16_t` for stored pitches.** The range tops out at 10 000 and a uint16
holds 65 535, so pitches fit in half the space of a 32-bit phase increment.
Inspecting the array also shows a readable `3400` rather than `292057776`.

**Fixed-size arrays, not dynamic allocation.** 20 KB is small enough that
resizable storage buys nothing, and `malloc` in a system with a 50 kHz
interrupt brings fragmentation and unpredictable timing.

**Arrays sized `[10]`, slot 0 unused.** Keys are numbered 1–9, so index N holds
key N and there is no subtraction anywhere to get wrong later.

**One conversion function.** `adc_to_phase_incr()` is called by both the
recording and the playback path, so the two cannot drift apart when the range
changes.

**Floating point outside the ISR only.** The conversion uses `float`, which is
fine at 100 Hz in a thread. Fixed point exists so the interrupt finishes inside
20 µs; nothing in the ISR uses floats.

### Open design question

`*` currently **arms** recording for one key and disarms on release, and keys
1–9 play back in normal mode without entering any mode. An earlier version had
`*` toggle a mode, with the first press of a key recording and the second
playing. The current behaviour matches the lab text and Hunter's forum answer
about pressing `*` between each note, and it lets recordings persist for
compose mode in week 3. The earlier design is preserved at commit `ca9cdfb`.

---

## 5. Bug log

Bugs found by review after week 2 and the commits that fixed them.

| # | Symptom | Cause | Fixed in |
| --- | --- | --- | --- |
| 1 | Record and play behaved randomly | `recorded[]` was a non-static local in a protothread. Protothreads resume by jumping into a `switch`, skipping the declaration's initialiser, and non-static locals do not survive a yield | `8f8cfce` |
| 2 | Silent memory corruption on key 9 | `record_key` ranges 1–9 but the arrays were sized `[9]`, valid indices 0–8 | `8f8cfce` |
| 3 | Playback sounded like the slider | No mode gate — the ADC thread wrote the pitch unconditionally while the playback thread wrote it too, both at 100 Hz | `b44499f` |
| 4 | Board booted silent, key 0 did nothing | `tone` initialised false and no `possible_key == 0` case existed | `b44499f` |
| 5 | Slider only reached 4095 Hz | The raw ADC value went straight in as the frequency | `42adcbb` |
| 6 | Would have broken recordings when fixing #5 | The pot→pitch conversion existed in two places | `42adcbb` |
| 7 | Loud pop on mute | Muting sent a data field of 0 (0 V) rather than mid-scale 2048 | `42adcbb` |
| 8 | Recordings vanished after toggling record mode | Entering record mode cleared every `recorded[]` flag | `42adcbb` |
| 9 | Playback could not be interrupted | The loop never re-checked `playing` and read `record_key` live | `42adcbb` |
| 10 | LED blink meaningless | Two threads toggled GPIO 25 | `42adcbb` |
| 11 | 176 KB of RAM for unused capacity | `MAX_SAMPLES` was 10 000, i.e. 100 s per key | `42adcbb` |
| 12 | Four comments stated the opposite of the code | "Set a row high" above a line driving it low; "pulldown" above `gpio_pull_up`; "10 s" for 10 ms | `42adcbb` |

**Pattern:** five of the twelve are the same mistake — the same fact stored in
two places. Two copies of the conversion; a `recorded[]` flag beside the length
that already implied it; two threads writing one pitch; two owning one LED;
comments disagreeing with their code.

---

## 6. AI prompt log

Tool: Claude (Claude Code), used across two sessions on 2026-09-04 and
2026-09-10. Every AI-assisted commit carries a `Co-Authored-By` trailer, so
`git log` is the primary record:

```
git log --format='%h %s %(trailers:key=Co-Authored-By,valueonly)'
```

### Code changes to `Lab1_Birdsong/dactest.c`

| Commit | Lines | Author | What |
| --- | --- | --- | --- |
| `aac577c` | +125 −0 | starter | Hunter's `a_Timer_Interrupt_DDS_Demo`, unmodified |
| `64e7d0b` | +160 −7 | Nina | ADC thread, channel B, keypad scan (written in lab; committed with AI help) |
| `ca9cdfb` | +435 −278 | Nina | Debounce state machine, record mode, playback thread |
| `8f8cfce` | +10 −3 | AI | Bugs 1 and 2 |
| `b44499f` | +15 −4 | AI | Bugs 3 and 4 |
| `42adcbb` | +52 −62 | AI | Bugs 5–12 and the record-mode restructure |
| `388fd74` | +10 −2 | AI | Replaced `?:` with `if`/`else` (the ternary is not used anywhere in the course demos) |

**Totals for the lab source file:**

- Written by Nina: **+595 −285**
- Suggested by AI: **+87 −71** across four commits
- Accepted: **all of them** (87 insertions, 71 deletions)
- Rejected / reverted: **none**

### What was asked, and what came back

| Asked | AI response | Accepted |
| --- | --- | --- |
| Explain the lab, set up the toolchain | Installed SDK 2.3.0, Arm GCC 14.2, CMake, Ninja, VS Code extensions; created the repo | yes |
| "what is wrong with my code" | Review listing 4 critical bugs, 2 sound bugs, 1 design question, 5 minor | reviewed |
| "fix 1 and 2" | +10 −3 | yes |
| "fix 3 and 4" | +15 −4 | yes |
| "is there anything else to fix" | Found 3 further issues not in the first review, including the vanishing recordings | reviewed |
| "fix all" | +52 −62, including a design change to record mode | yes |
| "is there anything more advanced than the class" | Checked each construct against the course demo repo; found `?:` used 0 times there | yes, +10 −2 |
| Explanations only (no code) | Debouncing, DDS, SPI, protothreads, matrix keypads, the C syntax of the state machine | n/a |

### Non-source changes

`build.sh`, `README.md` and `.gitignore` are build tooling, not lab code. They
were AI-written: `958ee7c`, `d5fc679`, `0baf665`, `d2ece5f`.

### Notes for the report

Two reference pages were produced during the work and may be cited:

- Field guide (setup, concepts, wiring diagrams, weekly walkthrough)
- Fix log (all twelve fixes with before/after code)

---

## 7. Still to do

### Before the week 3 checkout

- [ ] Playback at 8–10× speed (advance the index by 8 instead of 1)
- [ ] `#` compose mode: record a key sequence, replay the phrase
- [ ] Amplitude envelope — attack, sustain, decay — to remove the click on
      note boundaries. Required for the report's scope trace
- [ ] Re-measure ISR timing after the envelope is added
- [ ] 5730 only: external switch so the pot sets volume instead of frequency

### Report deliverables

- [ ] Scope trace of a swoop showing rise, sustain and fall
- [ ] Spectrogram of the MCU's own output (aux cable into the laptop, then
      Audacity / WaveForms / Python, or the Merlin app)
- [ ] Heavily commented code listing
- [ ] This prompt log, with final numbers
- [ ] Photograph of the breadboard

### Demo

- [ ] Play a sequence that imitates the cardinal song in Fig. 2
- [ ] Record and play back a random sequence the TA creates
- [ ] No resets and no reprogramming at any point during the demo
