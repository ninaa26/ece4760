# Lab notebook — Lab 2, Digital Galton Board

ECE 4760 (undergraduate), Cornell, Fall 2026
Board: Raspberry Pi Pico 2 / RP2350
Field guide: https://claude.ai/artifact/1DHuDbKJNWfoRbP3T7d65Z

Fields written as `___` still need to be filled in from the bench. Don't write
a number here that wasn't read off an instrument or the screen.

---

## 1. Timeline

| Date | Work |
| --- | --- |
| 2026-09-23 | VS Code set up. `Lab2_Galton/` copied from the course Animation Demo (GitHub version of 15 Sep 2026). VGA adapter and encoder on a fresh breadboard. **Week 1, step 1 working on the board** (the unmodified demo shows two balls bouncing in a box), on the second monitor tried. |

---

## 2. Hardware as built

A fresh breadboard; nothing is carried over from Lab 1.

| Part | Connection | Notes |
| --- | --- | --- |
| Pico 2 | lies along the breadboard, USB at the left end | pins 40 → 21 along the top edge, 1 → 20 along the bottom |
| 4760 VGA Adapter Board (V. Hunter Adams) | its 7-pin header sits one hole above Pico pins 27 → 21, in the same numbered strips | order left to right: RED, BLUE, H GREEN, L GREEN, GND, VSYNC, HSYNC = GP21, GP20, GP19, GP18, GND, GP17, GP16. The four colour resistors are on the adapter; values ___ |
| VGA cable | adapter → monitor | |
| Rotary encoder, Bourns PEC11 | A → GP2 (pin 4), B → GP3 (pin 5), C → GND | as in the group's encoder code; part number ___; not yet pushed into the breadboard (wires on its legs) |
| Encoder push switch | → GP4 (pin 6) and GND | not wired yet; needed for week 3 |
| MCP4822 DAC + audio jack | GP5/6/7 → CS/SCK/SDI, VOUTB → jack | added at step 6 |
| Reset button | none | flash with BOOTSEL held while plugging in USB |

---

## 3. Bench log

### Step 1 — the demo, unmodified (2026-09-23)

1. Flashed `Lab2_Galton` (the untouched demo). **Monitor 1 stayed plain black**
   with its input on VGA. It didn't show a "no signal" message.
2. Flashed `tools/vga-test`: four full-height colour stripes, and the on-board
   LED toggled every 30 frames. **LED blinked about once a second, but monitor 1
   was still black.** A 1 s blink means the Pico was producing 60 frames per
   second, so the chip, the VGA library and the build were all fine.
3. Checked the wiring from an overhead photo. The adapter header is in the same
   numbered strips as Pico pins 27–21, HSYNC is on pin 21, and nothing is in a
   power rail.
4. **Monitor 2 showed the demo correctly.** Cause: monitor 1 (model ___).
   It didn't accept the Pico's 640 × 480 signal, or its VGA input or cable was
   faulty; not narrowed down further.

Lesson for the report: blink an LED from the frame loop to split "the Pico
isn't producing frames" from "the frames don't reach the screen."

### Step 2 — rotary encoder (2026-09-23)

The group wrote its own encoder program: an interrupt on A's falling edge, a
3 ms time-based debounce, and B read at that moment to get the direction.
On the board it sometimes needed 2 clicks to change the count (23 Sep).
Claude pointed out two ways that version could miscount (A also rattles as it
opens, half-way through a clockwise click, when B is already LOW; and the
datasheet allows up to 5 ms of bounce against a 3 ms filter), and changed it
to interrupt on both edges of A and B and follow the four-state quadrature
sequence with a lookup table, counting only when the knob is back at rest.
Checked on the laptop: 10 clicks each way exact, including 4 rattles on every
edge. Merged into the demo as week 1 step 2 in `Lab2_Galton/animation.c`.
The fixed version is in `Lab2_Galton/animation.c` (guide step 3) but was not
flashed this session. Accuracy test on the board (10 clicks each way, slow and
fast): ___

### Flashing notes

- The Mac only sees the Pico in BOOTSEL mode. The course demos don't enable USB
  serial, so a running Pico doesn't show up over USB at all.
- `./flash.sh` builds, waits up to 2 minutes for the RP2350 drive, and copies the
  program. If the build fails, it now stops and lists the errors instead of
  flashing the previous `.uf2`.

---

## 4. AI use (for the report's prompt log)

Claude (Claude Code) was used on 2026-09-23 for:

- The field guide (requirements, wiring, explanations, week 1 step list).
- The week 1 edits to `animation.c`, shown step by step in the guide. Each step
  compiled; per-step counts of lines added and removed are shown in the guide.
  Which edits were typed as given and which were changed: ___
- `tools/vga-test` (the colour-stripe test).
- The fix to the group's encoder code (both-edge quadrature table), and the
  guide generator in `tools/lab2-guide/`.
- The `flash.sh` fixes (show build errors; work with folders like `tools/vga-test`)
  and the VS Code tasks.

Words exchanged: ___ (take from the session transcript when writing the report)
