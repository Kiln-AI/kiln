#!/usr/bin/env bash

# Build the web ui
cd "$(dirname "$0")"

if [[ $* != *--skip-web* ]]; then
  cd ../web_ui
  npm run build
  # Needs to run from this directory
  cd ../studio
fi

sleep 1 && open "http://localhost:8757" &
fastapi dev --port 8757 server.py
