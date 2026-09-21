#!/bin/zsh
# Double-click me in Finder to open the live spectrogram window.
cd "$(dirname "$0")"
exec /usr/bin/python3 live.py "$@"
