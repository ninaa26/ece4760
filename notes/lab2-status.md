# Lab 2 status and handoff

Last updated 2026-09-23. Read `CLAUDE.md` first for how to work with the
student.

## Where things stand

The week 1 checkoff is at the end of the lab section, week of 9/21 (this week).
It follows the guide's Week 1 tab, six steps from the course Animation Demo.

| Step | What | Code | On the board |
| --- | --- | --- | --- |
| 0 | Set up: VS Code, `Lab2_Galton/` copied from the GitHub demo (15 Sep 2026 version) | done | done |
| 1 | Unmodified demo: two balls in a box | no changes | **Works** (23 Sep). Monitor 1 stayed black; monitor 2 worked |
| 2 | Rotary encoder: count on screen, +1 clockwise, −1 counter-clockwise | done | The group's first version ran, but **sometimes needed 2 clicks per count**. The fixed version has **not been flashed yet** |
| 3 | Trim to one core, spare-time readout, late-frame LED | done | The student ran step 3 with the first encoder version |
| 4 | One ball falling under gravity | in the guide, compiles | not started |
| 5 | One peg, collision and bounce | in the guide, compiles | not started |
| 6 | DMA "thunk" through the MCP4822 DAC | in the guide, compiles | not started; DAC not wired yet |

`Lab2_Galton/animation.c` currently holds **guide step 3 with the fixed
encoder** (built, no warnings). Flashing it was tried three times this session
and timed out each time: the student wasn't at the bench to press BOOTSEL.

## The encoder story (worth knowing for the report and the quiz)

1. The group wrote its own encoder code: interrupt on A's falling edge, a 3 ms
   time-based debounce, then read B for the direction.
2. On the board it sometimes took 2 clicks to change the count. Cause: A also
   rattles when it *opens*, half-way through a clockwise click, while B is
   already LOW. A rattle there counts −1 against the click's +1. The datasheet
   also allows up to 5 ms of bounce against the 3 ms filter.
3. Fix (kept the group's names and structure): interrupt on both edges of A
   and B, follow the four-state quadrature sequence with a 16-entry table, and
   count only when the knob is back at rest (A = B = 1). Rattle adds +1 then −1
   and cancels.
4. Checked on the laptop (`tools/lab2-guide/test_encoder.sh`): 10 clicks each
   way exact, including 4 rattles on every edge, and a half-click nudge
   returns to 0.
5. Not checked on the board yet. If it's always exactly 2 clicks per count,
   the encoder is the 24-detent/12-pulse type: count at state 0 too
   (`new_state == 3 || new_state == 0`).

## Next steps

1. Flash `Lab2_Galton` (`./flash.sh Lab2_Galton`, then BOOTSEL) and do the
   10-click test: 10 clockwise slowly, 10 back, then fast. It should go
   0 → 10 → 0. Record the result in `notes/lab2-notebook.md`.
2. Guide steps 4, 5, 6, one at a time, flashing and checking after each.
3. Step 6 needs the DAC wired (table in the guide's step 6).
4. Checkoff: the list and the "be ready to explain" table are at the end of
   the guide's Week 1 tab.

## Still to fill in (`___` in the notebook)

The encoder part number (detents and pulses), the adapter's resistor values,
monitor 1's model, the 10-click result, and the spare time with one ball.

## Where everything is

| What | Where |
| --- | --- |
| Lab code | `Lab2_Galton/` (course demo copy; only `animation.c` and, from step 6, `CMakeLists.txt` change) |
| Field guide | https://claude.ai/artifact/1DHuDbKJNWfoRbP3T7d65Z · copy in `docs/ECE4760_galton-lab-field-guide.html` |
| Guide generator (edits, text, build check) | `tools/lab2-guide/` (see its README) |
| Lab notebook (hardware, bench log, AI-use log) | `notes/lab2-notebook.md` |
| Bench photo | `notes/figures/lab2-bench-2026-09-23.jpg` |
| VGA test program | `tools/vga-test/` |
| Requirements summary (another session's notes; may exist only in that worktree) | `notes/lab2-requirements.md` |
