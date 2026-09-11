#!/usr/bin/env zsh
# Build a project and copy it to the board.
#
#   ./flash.sh                  # builds Lab1_Birdsong and flashes it
#   ./flash.sh Lab1_Birdsong_NoEnvelope
#
# If the board is not in bootloader mode yet it waits for you, so you can run
# this first and then double-press the reset button.

set -e
ROOT="${0:A:h}"
PROJ="${1:-Lab1_Birdsong}"

"$ROOT/build.sh" "$PROJ" | tail -6
UF2=$(ls "$ROOT/build/${PROJ}-pico2/"*.uf2 2>/dev/null | head -1)
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
cp "$UF2" "$DRIVE"/ 2>/dev/null || true
sleep 3
if [[ -d "$DRIVE" ]]; then
  echo "WARNING: $DRIVE is still mounted — the copy may not have taken."
else
  echo
  echo "FLASHED. The drive ejected itself, which means the board is running it."
  echo "Press 1-6 for the cardinal presets.  # then 1 2 1 2 3 then # for a phrase."
fi
