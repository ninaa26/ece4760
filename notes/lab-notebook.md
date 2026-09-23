# Lab notebook — Lab 1, Synthesizing Birdsong

ECE 4760, Cornell, Fall 2026
Group members: ___
Board: Raspberry Pi Pico 2 / RP2350
Repo: https://github.com/ninaa26/ece4760

Fields written as `___` still need a measurement taken at the bench. Do not
write a number here that was not read off an instrument.

---

## 1. Timeline

| Date | Work |
| --- | --- |
| 2026-09-04 | Toolchain built and verified; repo created; Lab 1 project started from Hunter's `a_Timer_Interrupt_DDS_Demo`. Week 1 lab session. |
| 2026-09-10 | Week 2 work: keypad integrated, debounce state machine, record mode, playback thread. Code review, twelve bugs fixed, amplitude envelope added. |
| ___ | Weeks 1, 2 and 3 all checked off. Lab 1 now in the report stage. |

---

## 2. Development environment

| Component | Version | Location |
| --- | --- | --- |
| Pico C/C++ SDK | 2.3.0 | `~/Developer/pico-sdk` |
| Arm GNU toolchain | 14.2.Rel1 | `~/.pico-sdk/toolchain/14_2_Rel1` |
| CMake | 4.4.3 | Homebrew |
| Ninja | 1.13.2 | Homebrew |
| Host | macOS, Apple Silicon | |

`PICO_SDK_PATH` and `PICO_TOOLCHAIN_PATH` are exported from `~/.zshrc`.
`./build.sh <project>` wraps cmake and ninja and resolves every path relative to
itself, so the repo builds from a clean clone in any directory (verified).

### Environment problems worth recording

**Homebrew's `arm-none-eabi-gcc` has no C library.** It compiles happily and
then fails at link:

```
arm-none-eabi-ld: cannot find -lg: Invalid argument
arm-none-eabi-ld: cannot find -lc: Invalid argument
```

The Homebrew formula ships without newlib. Replaced with the official Arm GNU
toolchain, unpacked to `~/.pico-sdk/toolchain/`, and the Homebrew version was
removed so it could not shadow the working one. Symptom to remember: those two
specific `-lc` / `-lg` errors mean a compiler with no standard library, not a
problem with your code.

**`printf` does not come out of the USB cable.** None of the course demos
enable USB stdio, and the SDK default sends stdout to **UART0 on GPIO 0 (TX)
and GPIO 1 (RX)**. `screen /dev/tty.usbmodem*` shows nothing no matter how
correct everything else is. Either attach a USB-to-serial adapter to GPIO 0, 1
and ground, or add to `CMakeLists.txt`:

```
pico_enable_stdio_usb(birdsong 1)
pico_enable_stdio_uart(birdsong 0)
```

**Each project needs `pico_sdk_import.cmake` beside its `CMakeLists.txt`.**
Absent, cmake fails on the `include()` line before doing anything useful.

---

## 3. System as built

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
| GPIO 25 | on-board LED | heartbeat, owned by the keypad thread only |
| DAC pin 6 (VOUTB) | scope probe and audio jack tip | jack sleeve to ground |
| pin 30 (RUN) ↔ pin 28 (GND) | reset push button | double-press enters bootloader |

**Keypad pin order.** The lab's 3×4 keypads are labelled
`Col1 Col2 Col3 Row1 Row2 Row3 Row4 NC` along the header. The comment at the
top of the course `keypad.c` describes a different part and lists the rows
first. Wire by function, not by the pin numbers in that comment — wiring it the
other way makes every key read as −1.

**Row resistors.** Each row output needs a 330 Ω series resistor. Pressing two
keys in the same column ties one row output directly to another; if one is
driving high and the other low they fight, and the resistors limit that
current. The three column wires need nothing.

**Potentiometer pinout** (Adafruit 4219, datasheet `4219_C11375.pdf`). The
CIRCUIT drawing on page 1 shows pins 1 and 3 as the ends of the resistive track
and the arrow into the middle — pin 2 — as the wiper. Taper B, i.e. linear, so
pitch tracks slider position evenly. 60 mm of travel. The four larger holes in
the drawing (`4-Ø1.7`) are mounting points, not electrical.

**Reset button.** The project links `pico_bootsel_via_double_reset`, so two
presses within about 200 ms enter the bootloader. The USB cable never has to
come out to reflash.

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
| `ATTACK_TIME` | 250 | ISR ticks = 5.0 ms rise |
| `DECAY_TIME` | 250 | ISR ticks = 5.0 ms fall |
| `max_amplitude` | `int2fix15(1)` | full scale, 1.0 in fix15 |
| SPI baud | 20 MHz | 16-bit frames, mode 0 |

Build: `text 27,652 · bss 24,520` of the RP2350's 520 KB.

### Concurrency structure

| Runs | Rate | Job |
| --- | --- | --- |
| `alarm_irq` (ISR) | 50 000 Hz | envelope, DDS, sine lookup, SPI write |
| `protothread_toggle25` | 100 Hz | read pot, set pitch, append to a recording |
| `protothread_playback` | 100 Hz | step a stored recording back out |
| `protothread_core_0` | 33 Hz | scan keypad, debounce, set modes |

The protothreads library uses the free-running 64-bit system counter via
`time_us_64()` and **does not claim a hardware alarm**, so alarm 0 is free for
the audio interrupt. (The equivalent PIC32 library did claim a timer, which is
what the prep sheet's question 2 is pointing at.)

### Operating the instrument

| Key | Action |
| --- | --- |
| `0` | tone generator on / off; also cancels record, playback and compose |
| `*` | arm recording for the next key pressed |
| `1`–`9` | while armed: record. While composing: add to the phrase. Otherwise: play that key back |
| `#` | compose mode: first press starts a phrase, second press plays it |

Keys 1–9 power up holding Northern Cardinal presets (syllables on 1–6, full
songs on 7–9). Recording over a key replaces its preset.

Recording a swoop: tap `*`, press and hold a key, sweep the slider, release.
Playing it: tap that key. Recordings persist until deliberately overwritten.
The slider is ignored during playback.

---

## 4. Numerical characterisation

| Quantity | Value | Where it comes from |
| --- | --- | --- |
| Phase increment formula | `f × 2³² / Fs` | the DDS relation |
| Increment at 10 kHz | 858 993 459 | fits a 32-bit unsigned comfortably |
| Frequency resolution | `Fs / 2³²` = 1.164 × 10⁻⁵ Hz | one unit of increment |
| Nyquist limit | `Fs / 2` = 25 000 Hz | |
| Highest output used | 10 000 Hz | 40 % of Nyquist |
| Samples per cycle at 10 kHz | 5.0 | why the top of the range looks steppy on the scope |
| Samples per cycle at 2 kHz | 25.0 | |
| ISR ticks per stored pitch | 500 | 50 000 ÷ 100 — why 100 Hz storage sounds continuous |
| SPI transfer time | 0.80 µs | 16 bits at 20 MHz = 4 % of the 20 µs budget |
| DAC resolution | 12 bits, 0–4095 | gain 1×, so 0–2.048 V |
| ADC resolution | 12 bits, 0–4095 | over 0–3.3 V |

The steppiness at the top of the slider's range is expected, not a fault: five
samples per cycle is a legitimate reconstruction well below Nyquist, and it is
worth mentioning in the report rather than presenting as a defect.

### Four different things called "frequency"

Naming that repeatedly caused confusion, worth stating explicitly in the
report:

| Name | Value | What it is |
| --- | --- | --- |
| `Fs`, audio sample rate | 50 000 Hz | how often the ISR produces one sample |
| the pitch | 0–10 000 Hz | the number stored and heard; what the pot sets |
| recording rate | 100 Hz | how often the pot is sampled while recording |
| keypad scan rate | 33 Hz | how often the keys are read |

"Store the frequency at ~100 Hz" means the *thing stored* is a pitch of a few
thousand hertz, and one of them is stored a hundred times a second.

---

## 5. Week 1

**Checkpoint:** DAC wired and producing a tone, confirmed on the scope and
through an audio jack; output moved to the second DAC channel; reset button
added; potentiometer wired and verified with the ADC demo; ADC and DDS
integrated so the slider sets the frequency over 0 to ~10 kHz.

**Concepts exercised:** GPIO and pin function muxing, hardware timer alarms and
interrupt service routines, Direct Digital Synthesis, SPI and the MCP4822
command word, ADC and the potentiometer as a voltage divider, Nyquist, and
oscilloscope measurement.

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

### Order the work was done in

Deliberately one change at a time, testing between each, so that when something
broke it was obvious which change broke it.

1. Flashed a pre-built `.uf2` before any wiring existed, to prove the laptop,
   cable and board all worked. From that point any failure had to be wiring or
   code, which is a much smaller search space.
2. Wired the DAC — power and ground first, then the three SPI lines, then LDAC
   to ground — and checked VDD/VSS twice before applying power.
3. Loaded the unmodified timer-interrupt DDS demo and looked at VOUTA on the
   scope.
4. Added the 3.5 mm jack and listened.
5. Moved the output to channel B by changing the configuration constant. A
   one-line change, and the point of it is to prove the DAC command word is
   understood rather than copied.
6. Wired the potentiometer and flashed the **ADC demo on its own**, watching
   values on the serial terminal. Testing it in isolation means a bad reading
   can only be wiring.
7. Integrated the two by adding the DDS code into the ADC demo rather than the
   reverse, following the lab page's advice.

### Observations

- The ISR timing pin already exists in the starter demo as `ISR_GPIO 2`, so the
  week 2 measurement requirement needs no new code — only a probe.
- The demo's default tone is 800 Hz, set by `phase_incr_main` being initialised
  from `(800.0*two32)/Fs`.
- Integration was done by putting the pot read in a protothread and leaving the
  ISR untouched. The ISR still only accumulates, looks up and ships.

### Problems and how they were resolved

- **Toolchain would not link.** Homebrew's `arm-none-eabi-gcc` compiled but
  failed with `cannot find -lc` / `cannot find -lg`. Cause: no newlib in that
  formula. Replaced with the official Arm GNU toolchain. See section 2.
- **Frequency mapping was wrong and went unnoticed.** The integration wrote
  `phase_incr_main = (adc_val*two32)/Fs`, which puts the ADC reading straight
  into the frequency slot — so the slider spanned 0–4095 Hz, not the 0–10 kHz
  the checkpoint asks for. A cardinal reaches 7 kHz, so the top of the sweep was
  unreachable. Not caught until the week 2 code review; fixed in `42adcbb`.

---

## 6. Week 2

**Checkpoint:** keypad wired and verified; key 0 toggles the tone on a clean
debounced press; `*` enters record mode; holding a key 1–9 records the
frequency while held; pressing that key again plays the recording back; ISR
execution time measured on the scope.

**Concepts exercised:** matrix keypad scanning, contact bounce and a four-state
debounce machine, protothreads and cooperative scheduling, sharing state
between a thread and an interrupt, array storage sizing, and amplitude
envelopes.

### Measurements

| Quantity | Value | Expected |
| --- | --- | --- |
| ISR pulse width on GPIO 2 | ___ µs | small fraction of 20 µs |
| ISR period on GPIO 2 | ___ µs | 20.0 |
| ISR duty cycle | ___ % | width ÷ 20 µs |
| ISR pulse width **before** the envelope | ___ µs | baseline |
| ISR pulse width **after** the envelope | ___ µs | wider: one 64-bit multiply added |
| Increase from the envelope | ___ µs | this is the code-characterisation result |
| Envelope rise time | ___ ms | 5.0 |
| Envelope fall time | ___ ms | 5.0 |
| Recording length, 2 s hold | ___ samples | ~200 at 100 Hz |
| Keys verified working | ___ | all twelve |

### Order the work was done in

1. Wired the keypad — seven wires plus four 330 Ω row resistors — and flashed
   the **keypad demo on its own**, pressing all twelve keys before merging
   anything. Same isolation principle as the ADC demo in week 1.
2. Copied the scanning loop into the Lab 1 project along with
   `pt_cornell_rp2040_v1_4.h`, and confirmed key numbers still printed while
   the tone was still playing. Two things coexisting was the milestone, before
   any behaviour was attached to a key.
3. Built the four-state debounce machine **around** the existing scan rather
   than modifying it: the scan already produces one number per pass, and the
   state machine was added where the `printf` had been.
4. Added record mode and a separate playback protothread.
5. Full code review, which found twelve defects (section 8), fixed in four
   commits.
6. Added the amplitude envelope.

### Observations

- The keypad demo prints the key index directly: `0`–`9` for the digits, `10`
  for `*`, `11` for `#`, and `-1` for nothing pressed. Convenient — for the
  digits the number printed *is* the key.
- The scan drives one row low at a time (`scancodes` are `0xE, 0xD, 0xB, 0x7`,
  each with a single zero bit) and reads three columns held high by the Pico's
  internal pull-ups. A column reading 0 identifies the closed switch.
- The demo already yields for 30 000 µs between scans, which is exactly the
  30 ms debounce sampling period wanted, so no timing had to be changed.
- The debounce machine needs two variables that survive between passes: the
  state, and the candidate key being watched. The candidate matters — it is
  what stops sliding a finger onto a different key reading as the same press
  continuing.
- The action must fire on the **transition** into PRESSED, not while sitting in
  PRESSED. The `case PRESSED` branch deliberately does nothing; that empty
  branch is what stops one resting finger firing 33 times a second.
- Recording had to go in the 100 Hz ADC thread rather than the 33 Hz keypad
  thread, because the lab asks for ~100 Hz storage. This was not obvious from
  the lab text and is the structural decision of the week.

### Problems and how they were resolved

Twelve defects, listed with causes and fixes in section 9. The ones that cost
the most time to understand:

- **Record and play behaved randomly.** Cause was subtle: `recorded[]` was a
  non-static local inside a protothread. Confirmed by reading the library's own
  macros — `LC_RESUME(s) switch(s) { case 0:` and
  `LC_SET(s) s = __LINE__; case __LINE__:` — which show that resuming jumps to
  a `case` label past the declaration, so its initialiser never re-runs and the
  storage is not preserved.
- **Playback fought the potentiometer.** Both the ADC thread and the playback
  thread wrote the pitch at 100 Hz with nothing arbitrating.
- **Recordings disappeared.** Entering record mode cleared every flag, so
  nothing survived a mode toggle.

---

## 7. Method and verification

Practices used throughout, worth stating because several of the bugs were
caught by them rather than by luck.

**One change at a time, tested between.** Every merge step above was verified
before the next began. Most of the lost time in this lab came from the one
place this was not done — the frequency mapping went in with the integration
and was not checked against the checkpoint's stated range.

**Each demo flashed standalone before integration.** The ADC demo and the
keypad demo were both run alone first, so a bad reading could only mean wiring.

**Design questions taken to the course forum** rather than guessed. Three
answers shaped the design directly: Bruce Land on recording length, Hunter
Adams on record-mode behaviour and on whether the recorded pitch follows the
slider, and Dennis Bui on using `uint16_t`. All three are cited in section 8.

**Datasheets read rather than assumed.** The potentiometer pinout came from the
CIRCUIT drawing in `4219_C11375.pdf`, not from guessing which leg was the
wiper. The keypad pin order came from the labels printed on the part, which
turned out to contradict the comment in the course demo.

**Limits measured, not estimated.** The storage ceiling in section 8 was found
by compiling at increasing array sizes until the linker refused, rather than by
arithmetic on the datasheet's RAM figure.

**Code checked against the course demo repository for idiom.** Before keeping a
construct, it was counted in Hunter's demos: `static inline` appears 12 times
and `(float)` casts 37 times, so both are in scope; the ternary `?:` appears
zero times, so two uses of it were rewritten as `if`/`else` in `388fd74`.

**Repository verified from a clean clone.** Cloned fresh into an empty
directory and built, which caught `build.sh` resolving paths from a hard-coded
home directory instead of from its own location (`d5fc679`).

---

## 8. Design decisions

**Store the pitch, not the audio.** A recording is a list of frequencies
sampled at 100 Hz, not a waveform. Audio would be 50 000 numbers a second;
pitches are 100 — five hundred times less. It also means playback can be sped
up 8–10× in week 3 without the pitch rising: speeding up a list of pitches
replays the same notes faster, where speeding up audio would raise every
frequency. The analogy is a player-piano roll rather than a tape.

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
Suggested on the course forum by Dennis Bui.

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
20 µs; nothing in the ISR uses floats — the envelope multiply is `multfix15`,
which is a 64-bit integer multiply and a shift.

**A linear amplitude envelope.** A note that starts and stops instantly is a
step change in amplitude, and a step contains energy at every frequency: you
hear a click, and the spectrogram shows a vertical smear across the whole band
at each note boundary. Ramping in over 5 ms and out over 5 ms removes both.

Linear was chosen because it costs one fix15 addition per sample. The
alternatives and their trade-offs:

| Envelope | Advantage | Cost |
| --- | --- | --- |
| Linear | one add per sample | slope changes abruptly at the corners, so a faint tick remains |
| Exponential | matches how physical things decay, sounds natural | a multiply per sample; never quite reaches zero |
| Raised cosine | smooth slope everywhere, cleanest attack | needs a table or a running oscillator |
| ADSR | expressive, standard in synthesis | a state machine and four parameters to tune |
| Gaussian | most compact in frequency, least spectral smearing | table-driven, no truly flat sustain |

Implementation follows the course beep-synthesis demo: `attack_inc` and
`decay_inc` are computed once at boot with `divfix(max_amplitude,
int2fix15(ATTACK_TIME))`, and the ISR adds or subtracts one increment per tick
until it reaches the ceiling or zero. At zero the sine is multiplied away and
the output sits at mid-scale 2048, which is silence — so muting no longer needs
a special case.

### Recording length

Bruce Land on the course forum: there is no specification, a minute per key is
probably overkill, and since the memory is ours, we may as well find out how
large an array the machine will take. Measured by building at increasing sizes
until the linker refused:

| `MAX_SAMPLES` | Seconds per key | Total RAM | Links? |
| --- | --- | --- | --- |
| 1 000 | 10 | 24 KB | yes ← chosen |
| 5 000 | 50 | 102 KB | yes |
| 10 000 | 100 | 200 KB | yes |
| 20 000 | 200 | 395 KB | yes |
| 24 000 | 240 | 473 KB | yes |
| 25 000 | 250 | 493 KB | yes — the largest that links |
| 26 000 | 260 | — | **no**, "will not fit in region" |

So the hard ceiling is about four minutes per key on a 520 KB part. 1000 was
chosen: a cardinal's whistle is well under a second, and at 8–10× playback a
three-second gesture becomes a 0.3-second chirp, so ten seconds per key is
already far more than the lab can use. Sitting at 493 KB would leave almost
nothing for the stack, and stack exhaustion does not announce itself.

### Record-mode behaviour

Hunter Adams on the course forum, asked whether several notes can be recorded
per `*` press: he imagined pressing `*` again between each note, found the
device easier to use when it defaults to *not* recording, and is happy for this
to be a design decision. Asked whether the recorded frequency follows the
potentiometer while a key is held: yes — the frequency being recorded is set by
the potentiometer, and the rate at which the ADC is read need not change from
~100 Hz.

Implemented accordingly: `*` **arms** recording for one key and disarms on
release, and keys 1–9 play back in normal mode without entering any mode. An
earlier version had `*` toggle a mode, with the first press of a key recording
and the second playing; that version also cleared every slot on entering record
mode, so recordings could not survive a mode toggle — which compose mode in
week 3 requires. The earlier design is preserved at commit `ca9cdfb`.

---

## 9. Bug log

Bugs found by review after week 2 and the commits that fixed them.

| # | Symptom | Cause | Fixed in |
| --- | --- | --- | --- |
| 1 | Record and play behaved randomly | `recorded[]` was a non-static local in a protothread. Protothreads resume by jumping into a `switch` (`LC_RESUME(s) switch(s) { case 0:`), skipping the declaration's initialiser, and non-static locals do not survive a yield | `8f8cfce` |
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
comments disagreeing with their code. Whenever a second copy of something the
program already knows appears, expect the two to drift.

---

## 10. Prep question answers

The prep sheet is from the 2021 PIC32 version of the course, so the reasoning
transfers but the numbers do not. Both are given.

**Q1 — maximum current per I/O pin, and summed across all pins.**
PIC32: read the Absolute Maximum Ratings table; it gives a per-pin limit and a
separate, much smaller, total-across-all-pins limit. RP2040/RP2350: each GPIO's
drive strength is configurable at 2, 4, 8 or 12 mA, and the practical ceiling
for the whole board is set by the Pico's 3.3 V regulator rather than by the
chip. Either way the takeaway is the same: a GPIO drives a signal, not a load.

**Q2 — what hardware do protothreads use?**
The point of the question is that you must not reuse whatever timer the library
has claimed. On the RP2040/RP2350 version used here, the library calls
`time_us_64()` — the free-running 64-bit system counter — and claims **no**
hardware alarm, so alarm 0 is available for the audio interrupt. The PIC32
version did claim a timer.

**Q3 — timer period for a 44 kHz interrupt from a 40 MHz clock, prescaler 1.**

```
40,000,000 / 44,000 = 909.09  →  909 timer cycles
```

On the RP2350 the same thing is expressed as a period in microseconds:
1/44 000 ≈ 22.7 µs. This project runs at Fs = 50 kHz, so `DELAY` is 20 µs.

**Q4 — DDS frequency resolution with a 32-bit accumulator.**
The smallest change is one unit of increment:

```
Fs / 2³²  =  44,000 / 4,294,967,296  ≈  1.02 × 10⁻⁵ Hz   (sheet's 44 kHz)
Fs / 2³²  =  50,000 / 4,294,967,296  ≈  1.16 × 10⁻⁵ Hz   (this project)
```

Far finer than anything audible. The accumulator's low bits carry
fractional-sample phase, so accuracy is limited by the clock, not the
arithmetic.

**Q5 — alternatives to a linear ramp.**
See the envelope table in section 7. The underlying tension: any sudden change
in amplitude spreads energy across all frequencies, heard as a click and seen
as a vertical smear on the spectrogram.

---

## 11. AI prompt log

Tool: Claude (Claude Code), used across two sessions on 2026-09-04 and
2026-09-10. Every AI-assisted commit carries a `Co-Authored-By` trailer, so
`git log` is the primary record:

```
git log --format='%h %s %(trailers:key=Co-Authored-By,valueonly)'
```

### Code changes to `Lab1_Birdsong/birdsong.c`

| Commit | Lines | Author | What |
| --- | --- | --- | --- |
| `aac577c` | +125 −0 | starter | Hunter's `a_Timer_Interrupt_DDS_Demo`, unmodified |
| `64e7d0b` | +160 −7 | group | ADC thread, channel B, keypad scan (written in lab; committed with AI help) |
| `ca9cdfb` | +435 −278 | group | Debounce state machine, record mode, playback thread |
| `8f8cfce` | +10 −3 | AI | Bugs 1 and 2 |
| `b44499f` | +15 −4 | AI | Bugs 3 and 4 |
| `42adcbb` | +52 −62 | AI | Bugs 5–12 and the record-mode restructure |
| `388fd74` | +10 −2 | AI | Replaced `?:` with `if`/`else` (the ternary appears nowhere in the course demos) |
| `06214f1` | +49 −13 | AI | Amplitude envelope, fix15 macros, fix15 sine table |

**Totals for the lab source file:**

- Written by the group: **+595 −285**
- Suggested by AI: **+136 −84** across five commits
- Accepted: **all of them**
- Rejected or reverted: **none**

### What was asked, and what came back

| Asked | AI response | Accepted |
| --- | --- | --- |
| Explain the lab; set up the toolchain | Installed SDK 2.3.0, Arm GCC 14.2, CMake, Ninja, VS Code extensions; created the repo; found and worked around the Homebrew newlib problem | yes |
| "what is wrong with my code" | Review listing 4 critical bugs, 2 sound bugs, 1 design question, 5 minor | reviewed |
| "fix 1 and 2" | +10 −3 | yes |
| "fix 3 and 4" | +15 −4 | yes |
| "is there anything else to fix" | Found 3 further issues not in the first review, including the vanishing recordings | reviewed |
| "fix all" | +52 −62, including a design change to record mode | yes |
| "is there anything more advanced than the class" | Checked each construct against the course demo repo; `static inline` used 12 times there and `(float)` 37 times, but `?:` zero times | yes, +10 −2 |
| "add envelope" | fix15 macros and a 5 ms linear attack/decay, following the beep demo | yes |
| Explanations only, no code | Debouncing, DDS, SPI, protothreads, matrix keypads, the C syntax of `switch`/`case`, what a recording actually contains | n/a |

### Non-source changes

`build.sh`, `README.md`, `.gitignore` and this notebook are tooling and
documentation, not lab code. They were AI-written: `958ee7c`, `d5fc679`,
`0baf665`, `d2ece5f`, `a2623b8`, `06214f1`.

### Reference pages produced during the work

- Field guide — setup, concepts, wiring diagrams, week-by-week walkthrough
- Fix log — all twelve fixes with before and after code

---

## 12. Capturing the report figures

### Scope trace: rise, sustain, fall

Required by the report. The envelope makes it capturable.

1. Probe the DAC output (pin 6, VOUTB); ground clip on any GND hole.
2. Timebase **10–20 ms/div**. The rise is 5 ms and the fall is 5 ms, so a
   held note of roughly 100 ms fits rise, sustain and fall on one screen.
3. Vertical **0.5 V/div**, with the trace centred — the wave sits on 2048,
   which is mid-supply, not ground.
4. Trigger on the rising edge, single-shot, then press a key. Single-shot is
   the trick: a repeating trigger will not hold a one-off note.
5. The envelope is the *outline* of the waveform, not the waveform itself. At
   this timebase the individual cycles blur into a filled shape whose upper and
   lower edges trace the envelope. That shape is the figure.

Annotate the capture with the three regions and the measured rise and fall
times.

### Spectrogram

Aux cable from the DAC output into the laptop's microphone input, then any of:

- Audacity — record, then switch the track view to Spectrogram
- WaveForms on the lab PC — Spectrum Analyzer, or the Scope's FFT view
- Python — `scipy.signal.spectrogram` on a WAV recording
- The Merlin app pointed at a speaker, which also tests whether it convinces

A good swoop appears as a clean line sweeping up and back down between about
2 kHz and 7 kHz. Vertical smears at the note boundaries would mean the envelope
is not working.

### ISR timing

Probe GPIO 2. Pulse width is execution time, the gap is 20 µs. Capture it both
with and without the envelope if possible — the difference is the cost of one
`multfix15`, and that comparison is exactly what "code characterisation" means
in the report.

### Code listing

`Lab1_Birdsong/birdsong.c`. Check before submitting that no comment contradicts
its line — four did, and they are logged in section 9.

### Photograph

Breadboard from directly above, with the keypad and potentiometer in place.

---

## 13. Still to do

Status: all three weekly checkoffs (weeks 1–3) passed, including the demo.
What is left is the report.

### Checkoffs — done

- [x] Week 1
- [x] Week 2
- [x] Week 3, including the demo: cardinal imitation, a TA-invented
      sequence recorded and played back, no resets or reprogramming
- [x] Amplitude envelope — 5 ms linear attack and decay
- [x] `#` compose mode

### Open questions for the report

- The code in this repo has no 8–10× playback speed-up and no 5730 volume
  switch. Were they not needed, or does the checked-off version of
  `birdsong.c` live somewhere else? The code listing in the report has to be
  the code that was demoed.
- ISR timing has not been re-measured with the envelope in (compare
  `Lab1_Birdsong` and `Lab1_Birdsong_NoEnvelope` on GPIO 2).

### Report deliverables

- [ ] Scope trace of a swoop showing rise, sustain and fall
- [ ] Spectrogram of the MCU's own output
- [ ] Heavily commented code listing
- [ ] This prompt log, with final numbers
- [ ] Photograph of the breadboard
- [ ] Fill every remaining `___` in this notebook
