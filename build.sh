#!/usr/bin/env zsh
# Build any demo/lab project from the terminal.
#
#   ./build.sh Lab1_Birdsong                 # Pico 2 (default)
#   ./build.sh ADC/Simple_Demo               # a path inside the demo repo
#   PICO_BOARD=pico ./build.sh Lab1_Birdsong # original Pico 1
#   DEBUG=1 ./build.sh Lab1_Birdsong         # unoptimised + symbols, for a debug probe
#
# Works from a fresh clone in any directory: everything is resolved relative to
# this script, not to a hard-coded home path.

set -e

# Where this script lives = the root of the repo.
ROOT="${0:A:h}"

# Respect an existing environment (e.g. a lab machine) before falling back.
export PICO_SDK_PATH="${PICO_SDK_PATH:-$HOME/pico-sdk}"
export PICO_TOOLCHAIN_PATH="${PICO_TOOLCHAIN_PATH:-$HOME/.pico-sdk/toolchain/14_2_Rel1}"
[[ -d "$PICO_TOOLCHAIN_PATH/bin" ]] && export PATH="$PICO_TOOLCHAIN_PATH/bin:$PATH"
export PATH="/opt/homebrew/bin:$PATH"

if [[ ! -d "$PICO_SDK_PATH" ]]; then
  echo "PICO_SDK_PATH does not exist: $PICO_SDK_PATH"
  echo "Clone it with:  git clone -b master --depth 1 https://github.com/raspberrypi/pico-sdk.git ~/pico-sdk"
  echo "then:           cd ~/pico-sdk && git submodule update --init --depth 1"
  exit 1
fi

BOARD="${PICO_BOARD:-pico2}"
REPO="$ROOT/Hunter-Adams-RP2040-Demos"

CMAKE_ARGS=()
SUFFIX=""
if [[ "${DEBUG:-0}" == "1" ]]; then
  CMAKE_ARGS+=(-DCMAKE_BUILD_TYPE=Debug)
  SUFFIX="-debug"
fi

if [[ -z "$1" ]]; then
  echo "usage: ./build.sh <project-folder>"
  exit 1
fi

# Accept a path relative to the repo root, a path inside the demo repo, or an absolute path
SRC="$1"
[[ -d "$SRC" ]]         || SRC="$ROOT/$1"
[[ -d "$SRC" ]]         || SRC="$REPO/$1"
SRC="${SRC:A}"

if [[ ! -f "$SRC/CMakeLists.txt" ]]; then
  echo "no CMakeLists.txt in $SRC"
  exit 1
fi

# Each project needs the SDK's import shim next to its CMakeLists.txt
[[ -f "$SRC/pico_sdk_import.cmake" ]] || cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" "$SRC/"

BUILD="$ROOT/build/${SRC:t}-$BOARD$SUFFIX"

cmake -S "$SRC" -B "$BUILD" -G Ninja -DPICO_BOARD="$BOARD" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "${CMAKE_ARGS[@]}" >/dev/null
cmake --build "$BUILD"

echo
echo "board:  $BOARD"
[[ -n "$SUFFIX" ]] && echo "build:  Debug (symbols, unoptimised)"
for f in "$BUILD"/*.elf(N); do
  echo "elf:    $f"
done
for f in "$BUILD"/*.uf2(N); do
  echo "uf2:    $f"
done
echo
echo "To flash: hold BOOTSEL, plug in USB, then"
echo "   cp $BUILD/*.uf2 /Volumes/RP2350/"
