#!/bin/sh
set -eu
test "$#" -eq 1 || { echo "Usage: sh build-native.sh /path/to/new-output-directory" >&2; exit 2; }
src=$(CDPATH='' cd -- "$(dirname -- "$0")/native" && pwd)
mkdir -- "$1"
cc -O2 "$src/shadow-link-dock.c" -o "$1/shadow-link" \
    $(pkg-config --cflags --libs gtk+-3.0 gio-unix-2.0) -lm
cc -O2 "$src/shadow-terminal-gtk-v3.c" -o "$1/shadow-terminal-gtk-v3" \
    $(pkg-config --cflags --libs gtk+-3.0 vte-2.91)
