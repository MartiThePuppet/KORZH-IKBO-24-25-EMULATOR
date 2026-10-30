#!/usr/bin/env bash
# Тест: запуск с VFS + отладочный вывод
set -e
cd "$(dirname "$0")/.."
./run.sh --debug -v vfs_data/deep.json -s startup/startup.txt
