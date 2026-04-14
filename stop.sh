#!/usr/bin/env bash
set -e

BASE_DIR="/home/skdev/zkclient"
PID_FILE="$BASE_DIR/zkclient.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "zkclient is not running"
    exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || true)

if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Stopped zkclient PID $PID"
else
    echo "Process not running, cleaning stale pid file"
fi

rm -f "$PID_FILE"
