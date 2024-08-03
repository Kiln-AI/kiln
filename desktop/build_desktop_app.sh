#!/usr/bin/env bash

# Should have installed via: pip install -U pyinstaller

# Needs to run from the root of the project
cd "$(dirname "$0")"
cd ..

# Builds the desktop app
# TODO: use a spec instead of long winded command line
pyinstaller --windowed --onedir --icon="../icon.png" --add-data "../taskbar.png:." --add-data "../../server/studio:./server/studio" -n fune --noconfirm --distpath=./desktop/build/dist --workpath=./desktop/build/work --specpath=./desktop/build --osx-bundle-identifier=net.scosman.fune --paths=. ./desktop/base.py
