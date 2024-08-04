#!/usr/bin/env bash

# Needs to run from this directory
cd "$(dirname "$0")"

sleep 1 && open "http://localhost:8759/fune" &
fastapi dev --port 8759 main.py
