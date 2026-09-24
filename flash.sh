#!/usr/bin/env zsh
# Build a project and copy it to the board.
#
#   ./flash.sh                  # builds Lab1_Birdsong and flashes it
#   ./flash.sh Lab1_Birdsong_NoEnvelope
#   ./flash.sh Lab2_Galton
#   ./flash.sh tools/vga-test   # colour stripes + blinking LED, to test a VGA setup
#
# If the board is not in bootloader mode yet it waits for you, so you can run
# this first and then double-press the reset button.

set -e
ROOT="${0:A:h}"
PROJ="${1:-Lab1_Birdsong}"

# Show the compiler's output in full if the build fails. Piping it through
# tail used to hide the failure, and the previous .uf2 got flashed instead.
if ! BUILD_LOG=$("$ROOT/build.sh" "$PROJ" 2>&1); then
  echo "$BUILD_LOG"
  echo
  echo "BUILD FAILED. Nothing was flashed. The errors, first one first:"
  echo "$BUILD_LOG" | grep -E ': (fatal )?error:' | head -5
  exit 1
fi
echo "$BUILD_LOG" | tail -6
UF2=$(ls -t "$ROOT/build/${PROJ:t}-pico2/"*.uf2 2>/dev/null | head -1)
[[ -n "$UF2" ]] || { echo "no .uf2 was produced"; exit 1; }

find_drive() {
  for V in /Volumes/RP2350 /Volumes/RPI-RP2; do
    [[ -d "$V" ]] && { echo "$V"; return 0; }
  done
  return 1
}

if ! DRIVE=$(find_drive); then
  echo
  echo "Waiting for the board — double-press the reset button,"
  echo "or hold BOOTSEL and re-plug the USB cable.  (ctrl-C to give up)"
  for i in {1..120}; do
    sleep 1
    DRIVE=$(find_drive) && break
  done
fi

if [[ -z "$DRIVE" ]]; then
  echo "No bootloader drive appeared. Nothing was flashed."
  exit 1
fi

echo "copying $(basename "$UF2") -> $DRIVE"
# Do NOT swallow errors here: a failed copy used to look identical to a
# successful one, because the board ejects the drive either way.
if ! cp "$UF2" "$DRIVE"/ ; then
  echo "The copy failed. Retrying once..."
  sleep 1
  cp "$UF2" "$DRIVE"/ || { echo "Still failing. Is that really the Pico drive?"; exit 1; }
fi
sleep 3
if [[ -d "$DRIVE" ]]; then
  echo "WARNING: $DRIVE is still mounted — the copy may not have taken."
else
  echo
  echo "FLASHED. The drive ejected itself, which means the board is running it."
  [[ "$PROJ" == Lab1_Birdsong* ]] || exit 0
  echo "  1  what-cheer-cheer-cheer   2.1 s   <- measured figures"
  echo "  2  what-cheer-cheer (low)    1.5 s   <- measured figures"
  echo "  3  cheer-cheer-cheer         2.0 s"
  echo "  4  birdy-birdy-birdy         1.6 s"
  echo "  5  purty-purty-purty         1.4 s"
  echo "  6  what-cheer + trill        2.3 s"
  echo "  7  rising series             1.7 s"
  echo "  8  slow downslurs            2.3 s"
  echo "  9  chip series               1.2 s"
fi
