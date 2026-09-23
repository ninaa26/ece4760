# What the example reports do well

Four reports the professor gave as examples of good work. All four are from
before the course's AI policy existed, so none has an AI section. Ours needs
one, both in Design and Testing and as the prompt log.

| Report | Lab | Platform | Length |
| --- | --- | --- | --- |
| Birdsong (Cupp, Pegels, Martucci) | Lab 1, birdsong | PIC32 | 16 pp, ~4 500 words |
| Birdsong 2 (Zou, Wang, Huang) | Lab 1, birdsong | PIC32 + keypad | 15 pp, ~4 500 words |
| Cricket (Beiler, Field, Reid Vicars) | Lab 1, cricket sync | RP2040 | 25 pp incl. code |
| Reaction wheel (Kain, Liang, Han) | Lab 3, PID pendulum | RP2040 | 28 pp incl. code |

Birdsong 2 is the closest match to our lab: a keypad, a four-state debounce
machine, and record and playback modes.

---

## The shape they share

1. **Introduction.** One paragraph: the goal, the method in one sentence each
   (DDS, keypad, modes), and what the finished system does.
2. **Design and testing**
   - **Concept.** The maths first, with numbers. Birdsong works out
     `0.130 s × 44 000 = 5720 samples`. Birdsong 2 derives the DDS equation
     `N = Fout · 2³² / Fs` and explains why the table has 256 entries and why
     the index is the top 8 bits.
   - **Hardware.** A photo of the build, a **table of components** with the
     job each one does, and a circuit diagram. Birdsong 2 explains *why* the
     keypad rows have series resistors.
   - **Software.** A **block diagram** of the ISR and threads and how they
     talk through globals. A **table of every function, thread and important
     variable** with what it does. A **state diagram of the debounce FSM**.
     Short code excerpts as numbered figures.
   - **Testing.** Told as a story of increments: what was tested alone
     first, then what was added, and how each step was confirmed. They name
     specific bugs, the symptom, how they found it (printf, scope, LED) and the
     fix.
3. **Results.** Every figure is numbered, captioned, referred to in the text,
   and followed by what it shows **with numbers checked against the spec**:
   - Birdsong measures the swoop as 130 ms and the ramps as 22.7 ms, converts
     to 998.8 samples, and concludes it is the specified 1000.
   - They read swoop frequencies off the spectrogram (1.74 to 2 kHz) and
     compare them with the handout.
   - They explain anomalies instead of hiding them. Birdsong's "silent"
     pause reads 40 mV on the scope; they say why and why it doesn't matter.
   - **Code speed:** the cycle budget per interrupt (909 cycles at 44 kHz on
     40 MHz) against what the ISR costs. Birdsong 2 reports 730 cycles going
     down to 680 after optimising.
   - What performed well, what performed poorly, what's unique about the
     implementation.
4. **Conclusions.** What they learned, the issues they hit, what they would
   do differently, and ideas for extensions.
5. **Appendix: code listing.**

The cricket report adds a **week-by-week benchmark table**
(week | software outcome | hardware outcome | testing method), which fits a
three-week lab well. The cricket and reaction reports cite their sources.

---

## Where that leaves ours

| They have | We have | Gap |
| --- | --- | --- |
| DDS maths with numbers | notebook §4: increment formula, resolution, Nyquist, samples per cycle | none, just write it up |
| Component table, circuit diagram, photo | wiring table (notebook §3) and field-guide diagrams | **schematic**, **photo** |
| Thread/ISR block diagram | concurrency table (notebook §3) | **draw the diagram** |
| Table of functions/threads/variables | spread over notebook §3 and §8 | pull into one table |
| Debounce state diagram | described in notebook §6 | **draw it** |
| Testing story with named bugs | notebook §5–7 and the 12-bug log (§9), more thorough than either birdsong example | none |
| Scope figures checked against the spec | nothing measured | **scope traces**: a swoop's rise, sustain and fall (the submitted code has no envelope, so decide how to handle this), ISR pulse |
| Spectrogram compared with the handout's Fig. 2 | tool ready, no capture | **spectrogram** of our Fig. 2 imitation against Fig. 2 |
| Code speed analysis | 20 µs budget at 50 kHz, 150 MHz = 3000 cycles per interrupt; measurement missing | **ISR pulse width**, tone on and off |
| Anomalies explained | known one: steppy waveform near 10 kHz (5 samples per cycle), notebook §4 | none |
| Week-by-week benchmarks | timeline (notebook §1), checkpoints (`lab1-requirements.md`) | put in the cricket-style table |
| Unique features | 10× speed-up by replay rate rather than resampling; recordings persist across modes | write it up |
| — (no AI policy then) | prompt log (notebook §11) | AI-use paragraph in Design and Testing |

We already have more on design reasoning and debugging than either birdsong
example. What we're missing is the measured evidence and the diagrams, which
are exactly what their Results sections are built on.
