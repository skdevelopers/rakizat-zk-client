#!/usr/bin/env bash
set -e

BASE_DIR="/home/skdev/zkclient"
PID_FILE="$BASE_DIR/zkclient.pid"
LOG_FILE="$BASE_DIR/logs/runner.log"

mkdir -p "$BASE_DIR/logs"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "zkclient already running with PID $OLD_PID"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

cd "$BASE_DIR"
source .venv/bin/activate

nohup python -m main >> "$LOG_FILE" 2>&1 &
NEW_PID=$!

echo "$NEW_PID" > "$PID_FILE"
echo "zkclient started with PID $NEW_PID"
