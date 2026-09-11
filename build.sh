#!/usr/bin/env zsh
# Build any demo/lab project from the terminal.
#   ./build.sh Audio/a_Timer_Interrupt_DDS_Demo
#   ./build.sh ~/Developer/ECE4760/Lab1            (any folder with a CMakeLists.txt)
# Produces a .uf2 and prints its path.

set -e

export PICO_SDK_PATH="$HOME/pico-sdk"
export PICO_TOOLCHAIN_PATH="$HOME/.pico-sdk/toolchain/14_2_Rel1"
export PATH="$PICO_TOOLCHAIN_PATH/bin:/opt/homebrew/bin:$PATH"

BOARD="${PICO_BOARD:-pico2}"          # PICO_BOARD=pico ./build.sh ... for a Pico 1

# DEBUG=1 ./build.sh <project>  -> unoptimised build with symbols, for use with a debug probe.
# Kept in its own build directory so it never collides with the normal build.
CMAKE_ARGS=()
SUFFIX=""
if [[ "${DEBUG:-0}" == "1" ]]; then
  CMAKE_ARGS+=(-DCMAKE_BUILD_TYPE=Debug)
  SUFFIX="-debug"
fi
REPO="$HOME/Developer/ECE4760/Hunter-Adams-RP2040-Demos"

if [[ -z "$1" ]]; then
  echo "usage: ./build.sh <project-folder>"
  exit 1
fi

# Accept either a path relative to the demo repo, or any absolute path
SRC="$1"
[[ -d "$SRC" ]] || SRC="$REPO/$1"
SRC="${SRC:A}"                         # absolute, symlinks resolved

if [[ ! -f "$SRC/CMakeLists.txt" ]]; then
  echo "no CMakeLists.txt in $SRC"
  exit 1
fi

# Each project needs the SDK's import shim next to its CMakeLists.txt
[[ -f "$SRC/pico_sdk_import.cmake" ]] || cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" "$SRC/"

BUILD="$HOME/Developer/ECE4760/build/${SRC:t}-$BOARD$SUFFIX"

cmake -S "$SRC" -B "$BUILD" -G Ninja -DPICO_BOARD="$BOARD" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "${CMAKE_ARGS[@]}" >/dev/null
cmake --build "$BUILD"

echo
echo "board:  $BOARD"
[[ -n "$SUFFIX" ]] && echo "build:  Debug (symbols, unoptimised)"
for f in "$BUILD"/*.elf; do
  echo "elf:    $f"
done
for f in "$BUILD"/*.uf2; do
  echo "uf2:    $f"
done
echo
echo "To flash: hold BOOTSEL, plug in USB, then drag that .uf2 onto the RP2350 drive"
echo "   or:    cp <that .uf2> /Volumes/RP2350/"
