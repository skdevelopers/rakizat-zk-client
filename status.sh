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
    echo "zkclient running with PID $PID"
else
    echo "zkclient not running but pid file exists"
fi
