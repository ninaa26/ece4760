# Working in this repo

Course work for ECE 4760 (Cornell, Fall 2026) on a Raspberry Pi Pico 2 (RP2350).
Several Claude accounts and sessions work on this repo. Memory is per account,
so anything the next session needs goes in this file or in `notes/`, not only
in chat or memory.

**Start here for Lab 2:** `notes/lab2-status.md` (where things stand, what's
next, what hasn't been checked on the board).

## How to work with the student

- **ECE 4760 undergraduate, not 5730.** Requirements marked 5730-only never apply.
- **No strong background in electronics or C.** Explain simply, at about a
  middle-school level, with everyday comparisons (a doorbell for an interrupt,
  counting in cents for fixed point, two whiteboards for double buffering).
  Put the plain-words version next to the technical one, not instead of it.
  Understanding is the goal: the TA checkoffs and the in-class debugging quiz
  test it.
- **The student builds the code themselves, starting from the course demos.**
  Don't hand over a finished program. Work in small steps, each checked on the
  board, and show every change: where it goes, the code, what it does.
- **The group writes code too.** When the student brings the group's own code,
  use it and fix it in place rather than replacing it with a different design.
  Say what was wrong and why.
- **Be clear about what's AI-written.** The lab report needs a prompt log for
  AI-generated code. Record it in the lab notebook (`notes/lab2-notebook.md`,
  section 4).
- **The lab handout is the spec.** It overrides Hunter Adams' demo videos and
  any older material: https://vanhunteradams.com/Pico/Galton/Galton.html
- Never write a measured number that wasn't read off an instrument or the
  screen. Leave `___` for the student to fill in.
- The repo is **public**: no names, emails or other personal details in
  committed files.

## Build and flash

    ./build.sh Lab2_Galton          # compile only
    ./flash.sh Lab2_Galton          # compile, wait up to 2 min for the board, copy
    ./flash.sh tools/vga-test       # colour stripes + blinking LED, to test a VGA setup

- There's no reset button on the Lab 2 board. To flash: unplug USB, hold
  BOOTSEL, plug back in. The Mac only sees the Pico in that mode: the course
  demos don't enable USB serial, so a running Pico doesn't show up over USB.
- If you start `flash.sh` in the background, tell the student right away that
  the 2-minute window is open. It times out quietly ("Nothing was flashed")
  if they aren't at the bench.
- VS Code: `.vscode/` has tasks (Cmd+Shift+B = build and flash Lab 2) and
  IntelliSense settings that read `build/Lab2_Galton-pico2/compile_commands.json`.
- Pico SDK: `~/Developer/pico-sdk`. Toolchain: `~/.pico-sdk/toolchain/14_2_Rel1`.
  The course demos are cloned (untracked) at `Hunter-Adams-RP2040-Demos/`;
  `git -C Hunter-Adams-RP2040-Demos pull` to update.

## Lab 2 hardware (as built, fresh breadboard)

| Part | Pico pins |
| --- | --- |
| 4760 VGA adapter board (resistors on it) | plugs in beside pins 21–27: HSYNC GP16, VSYNC GP17, GND, L GREEN GP18, H GREEN GP19, BLUE GP20, RED GP21 |
| Rotary encoder, Bourns PEC11 | A → GP2 (pin 4), B → GP3 (pin 5), C (middle pin) → GND |
| Encoder push switch | GP4 (pin 6) + GND. Not wired yet; needed in week 3 |
| MCP4822 DAC (step 6) | CS GP5, SCK GP6, SDI GP7; VOUTB → audio jack |
| On-board LED | GP25 |

## The Lab 2 field guide

https://claude.ai/artifact/1DHuDbKJNWfoRbP3T7d65Z — a copy is kept at
`docs/ECE4760_galton-lab-field-guide.html`.

- It's shared "anyone with the link", so any account can read it. Only the
  owning account, or one given edit access, can publish to it. Otherwise,
  publish a separate artifact and say so.
- Other sessions edit it too. Always read the live version before publishing
  and merge onto it. Never publish an old local copy over it.
- Week 1 steps 2–6 are generated from `tools/lab2-guide/` (see its README), so
  every code listing on the page is code that compiled. Steps 0–1, the checkoff
  and the other tabs are hand-edited HTML.

## Lab 1

Checked off. `Lab1_Birdsong/` is the code submitted with the report. The report
work is in `notes/report/` on `main`.
