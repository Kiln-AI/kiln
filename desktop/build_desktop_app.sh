#!/usr/bin/env bash

# Should have installed via: pip install -U pyinstaller

pyinstaller --windowed --onefile --icon="../icon.png" --add-data "../taskbar.png:." -n fune --noconfirm --distpath=./build/dist --workpath=./build/work --specpath=./build base.py
