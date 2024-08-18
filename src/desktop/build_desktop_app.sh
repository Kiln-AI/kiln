#!/usr/bin/env bash

set -e

# move to the root of the src
cd "$(dirname "$0")"
cd ..

if [[ $* != *--skip-web* ]]; then
  # build the web ui
  echo "Building web UI"
  cd web_ui
  npm install
  npm run build
  cd ..
fi

mkdir -p desktop/build

if [ "$(uname)" == "Darwin" ]; then
  echo "Building MacOS app"
  cp desktop/mac_taskbar.png desktop/build/taskbar.png
  cp desktop/mac_icon.png desktop/build/icon.png
  # onedir launches faster, and still looks like 1 file with MacOS .app bundles
  PLATFORM_OPTS="--onedir --windowed --osx-bundle-identifier=com.kiln-ai.kiln.studio"

  PY_PLAT=$(python -c 'import platform; print(platform.machine())')
  echo "Building MacOS app for single platform ($PY_PLAT)"
else
  echo "Building Windows App"
  cp desktop/win_taskbar.png desktop/build/taskbar.png
  cp desktop/win_icon.png desktop/build/icon.png
  # onefile launches slower, but compiles whole app into a single .exe
  # TODO: should use --windowed on Windows, but it doesn't work and needs debugging
  PLATFORM_OPTS="--onefile --windowed --splash=../win_splash.png"
fi

# Builds the desktop app
# TODO: use a spec instead of long winded command line
pyinstaller $(printf %s "$PLATFORM_OPTS") --icon="./icon.png" \
  --add-data "./taskbar.png:." --add-data "../../web_ui/build:./web_ui/build" \
  --noconfirm --distpath=./desktop/build/dist --workpath=./desktop/build/work \
  -n kiln --specpath=./desktop/build \
  --paths=. ./desktop/desktop.py

# MacOS apps have symlinks, and GitHub artifact upload zip will break them. Tar instead.
if [[ $* == *--compress-mac-app* && "$(uname)" == "Darwin" ]]; then
  echo "Compressing MacOS app"
  cd ./desktop/build/dist
  tar czpvf kiln.app.tgz kiln.app
  rm -r kiln.app
  cd ../../..
fi