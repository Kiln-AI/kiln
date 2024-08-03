#!/usr/bin/env bash

sleep 1 && open "http://localhost:8759/studio/index.html" &
fastapi dev --port 8759 main.py