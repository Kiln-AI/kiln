#!/usr/bin/env bash

# Build the web ui
cd "$(dirname "$0")"
cd ../studio/web_ui
# npm run build
# Needs to run from this directory
cd ../../server

sleep 1 && open "http://localhost:8757" &
fastapi dev --port 8757 server.py
