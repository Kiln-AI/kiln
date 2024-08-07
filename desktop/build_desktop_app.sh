#!/usr/bin/env bash

# Should have installed via: pip install pyinstaller

# move to the root of the repo
cd "$(dirname "$0")"
cd ..

# build the web ui
cd studio/web_ui
npm run build
cd ../..

APP_STYPE="--onefile"
if [ "$(uname)" == "Darwin" ]; then
  echo "Building MacOS app"
  APP_STYPE="--onedir"
fi

echo $APP_STYPE

# Builds the desktop app
# TODO: use a spec instead of long winded command line
pyinstaller --windowed $APP_STYLE --icon="../icon.png" \
  --add-data "../taskbar.png:." --add-data "../../studio/web_ui/build:./studio/web_ui/build" \
  -n fune --noconfirm --distpath=./desktop/build/dist --workpath=./desktop/build/work \
  --specpath=./desktop/build --osx-bundle-identifier=net.scosman.fune \
  --paths=. ./desktop/desktop.py
