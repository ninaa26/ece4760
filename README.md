# ECE 4760 / 5730 — Nina

Course work for Digital Systems Design Using Microcontrollers (Cornell, Fall 2025).
Board: Raspberry Pi Pico 2 (RP2350).

## Layout

| Path | What it is |
| --- | --- |
| `Lab1_Birdsong/` | My Lab 1 project. Started as an unmodified copy of `Audio/a_Timer_Interrupt_DDS_Demo` from Hunter Adams' course demo repo. |
| `build.sh` | Wrapper around cmake/ninja. Not lab code. |
| `Hunter-Adams-RP2040-Demos/` | Upstream demo code, cloned from https://github.com/vha3/Hunter-Adams-RP2040-Demos (gitignored) |
| `build/` | Build output, .uf2 files (gitignored) |
| `notes/` | Bench measurements and the AI prompt log the lab report requires |

## Build

    ./build.sh Lab1_Birdsong                 # Pico 2 (default)
    PICO_BOARD=pico ./build.sh Lab1_Birdsong # original Pico

Prints the path to the .uf2.

## Flash

Hold BOOTSEL, plug in USB, then:

    cp build/Lab1_Birdsong-pico2/*.uf2 /Volumes/RP2350/

## Serial

    ls /dev/tty.usbmodem*
    screen /dev/tty.usbmodem1101 115200      # ctrl-A then k to quit

## Environment

Set in `~/.zshrc`:

- `PICO_SDK_PATH=~/pico-sdk` — Pico SDK 2.3.0
- `PICO_TOOLCHAIN_PATH=~/.pico-sdk/toolchain/14_2_Rel1` — Arm GNU toolchain 14.2.Rel1

Do not use Homebrew's `arm-none-eabi-gcc`: it has no newlib and fails at link with
`cannot find -lc` / `cannot find -lg`.
