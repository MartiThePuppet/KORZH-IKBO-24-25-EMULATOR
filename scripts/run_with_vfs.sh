#!/usr/bin/env bash
# Тест этапа 2+3: запуск с VFS и стартовым скриптом, с отладочным дампом.
set -e
cd "$(dirname "$0")/.."
# --debug печатает параметры; -v подключает глубокую VFS; -s запускает скрипт.
./run.sh --debug -v vfs_data/deep.json -s startup/startup.txt
