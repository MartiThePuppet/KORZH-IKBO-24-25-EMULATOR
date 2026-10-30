#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec python -m src.shell_emulator "$@"
