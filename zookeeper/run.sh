#!/usr/bin/env bash
set -e

trap 'kill 0' EXIT

SERVICE_NAME=demo HOST=127.0.0.1 PORT=8001 uv run service.py &
SERVICE_NAME=demo HOST=127.0.0.1 PORT=8002 uv run service.py &
SERVICE_NAME=demo HOST=127.0.0.1 PORT=8003 uv run service.py &

wait
