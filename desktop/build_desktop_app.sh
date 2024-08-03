#!/usr/bin/env bash

pyinstaller --windowed --onefile --icon="../icon.png" --add-data "../taskbar.png:." -n fune --noconfirm --distpath=./build/dist --workpath=./build/work --specpath=./build base.py
