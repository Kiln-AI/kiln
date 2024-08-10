#!/usr/bin/env bash

set -e

# move to the root of the repo
cd "$(dirname "$0")"
cd ..

# build the web ui
cd studio/web_ui
npm install
npm run build
cd ../..

mkdir -p desktop/build


if [ "$(uname)" == "Darwin" ]; then
  echo "Building MacOS app"
  cp desktop/mac_taskbar.png desktop/build/taskbar.png
  cp desktop/mac_icon.png desktop/build/icon.png
  PLATFORM_OPTS="--onedir --osx-bundle-identifier=net.scosman.fune"
  ## TODO Add this here, but need to check this python install supports universal2
  ## --target-arch=universal2 
else
  echo "Building Windows App"
  cp desktop/win_taskbar.png desktop/build/taskbar.png
  cp desktop/win_icon.png desktop/build/icon.png
  PLATFORM_OPTS="--onefile"
fi

# Builds the desktop app
# TODO: use a spec instead of long winded command line
pyinstaller --windowed $(printf %s "$PLATFORM_OPTS") --icon="./icon.png" \
  --add-data "./taskbar.png:." --add-data "../../studio/web_ui/build:./studio/web_ui/build" \
  --noconfirm --distpath=./desktop/build/dist --workpath=./desktop/build/work \
  -n fune --specpath=./desktop/build \
  --paths=. ./desktop/desktop.py
