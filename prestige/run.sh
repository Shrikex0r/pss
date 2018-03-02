#!/bin/bash

echo "Launching the Pixel Starships Discord Bot"
echo "Press Ctrl-C twice to stop the bot"

while true; do
    python3 bot.py
    sleep 2
    echo "[run.sh] Relaunching bot.py....."
done
