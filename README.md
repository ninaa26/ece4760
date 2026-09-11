# ECE 4760 / 5730

Course work for Digital Systems Design Using Microcontrollers (Cornell, Fall 2025).
Board: Raspberry Pi Pico 2 (RP2350).

Field guide (setup, concepts, wiring diagrams, week-by-week walkthrough):
https://claude.ai/code/artifact/bb80ce5d-de5f-4b22-81be-ca5ed6dc881d

## Start from nothing

    git clone https://github.com/ninaa26/ece4760.git
    cd ece4760
    ./build.sh Lab1_Birdsong

`build.sh` resolves everything relative to itself, so the clone can live anywhere.
The only thing it needs on the machine is the Pico SDK; if `PICO_SDK_PATH` is
unset it looks in `~/pico-sdk` and prints the clone command if it is not there.

## Flash

Hold BOOTSEL, plug in USB, wait for the drive, then:

    cp build/Lab1_Birdsong-pico2/birdsong.uf2 /Volumes/RP2350/

The drive is `RP2350` on a Pico 2, `RPI-RP2` on a Pico 1. It unmounts itself the
moment the copy finishes — that is success. Ignore the macOS eject warning.

With the reset button wired (physical pin 30 RUN to pin 28 GND), two fast presses
enter the bootloader, so the cable never has to come out.

## Build options

    ./build.sh Lab1_Birdsong                  # Pico 2 (default)
    PICO_BOARD=pico ./build.sh Lab1_Birdsong  # original Pico 1
    DEBUG=1 ./build.sh Lab1_Birdsong          # unoptimised + symbols, for a debug probe
    ./build.sh ADC/Simple_Demo                # any project inside the demo repo

## Using the instrument

| Key | Does |
| --- | --- |
| `0` | tone generator on / off |
| `*` | arm recording for the next key pressed |
| `1`–`9` | while armed: record. Otherwise: play that key back |
| `#` | unused (compose mode, week 3) |

Recording a swoop: tap `*`, press and hold a key, sweep the slider, release.
Playing it: tap that key. Recordings persist until deliberately overwritten.
The slider sets pitch from 0 to 10 kHz; it is ignored during playback.

## Wiring

| Pico | Goes to |
| --- | --- |
| 3V3(OUT) | DAC pin 1 VDD, + rail |
| GND | DAC pins 7 VSS and 5 LDAC, − rail |
| GPIO 5 / 6 / 7 | DAC pins 2 CS, 3 SCK, 4 SDI |
| GPIO 2 | ISR timing pin, for the scope |
| GPIO 26 | potentiometer pin 2 (wiper); pins 1 and 3 to 3.3 V and GND |
| GPIO 9–12 | keypad rows, each via a 330 Ω resistor |
| GPIO 13–15 | keypad columns, direct |
| DAC pin 6 | VOUTB — audio out, to the scope and the jack tip |

Keypad header order on the lab's 3×4 units is
`Col1 Col2 Col3 Row1 Row2 Row3 Row4 NC` — wire by function, not by pin number.
The demo's header comment assumes a different part.

## Serial

`printf` goes to UART0 on GPIO 0 (TX) and GPIO 1 (RX), **not** over USB. Attach a
USB-to-serial adapter to those two pins plus ground:

    ls /dev/tty.usbserial* /dev/tty.usbmodem*
    screen /dev/tty.usbserial-XXXX 115200      # ctrl-A then k to quit

To send it over the USB cable instead, add to `Lab1_Birdsong/CMakeLists.txt`:

    pico_enable_stdio_usb(birdsong 1)
    pico_enable_stdio_uart(birdsong 0)

## What is in here

```
ece4760/
├── Lab1_Birdsong/          the lab project
│   ├── birdsong.c          all of the lab code — the only file you edit
│   ├── CMakeLists.txt      build recipe: sources and SDK libraries
│   ├── pt_cornell_rp2040_v1_4.h   protothreads (Bruce Land), unmodified
│   └── pico_sdk_import.cmake      SDK boilerplate, unmodified
├── notes/
│   ├── lab-notebook.md     measurements, design decisions, bug log, prompt log
│   └── figures/            scope traces and photos for the report
├── build.sh                cmake/ninja wrapper — build tooling, not lab code
└── README.md
```

Not tracked (see `.gitignore`): `build/` output, and
`Hunter-Adams-RP2040-Demos/` if you clone the reference demos alongside:

    git clone https://github.com/vha3/Hunter-Adams-RP2040-Demos.git

## Environment

- `PICO_SDK_PATH` — defaults to `~/pico-sdk` (SDK 2.3.0)
- `PICO_TOOLCHAIN_PATH` — defaults to `~/.pico-sdk/toolchain/14_2_Rel1`

Do not use Homebrew's `arm-none-eabi-gcc`: it ships without newlib and fails at
link with `cannot find -lc` / `cannot find -lg`.
