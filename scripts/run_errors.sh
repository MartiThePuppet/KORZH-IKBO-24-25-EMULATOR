#!/usr/bin/env bash
# Тест: обработка ошибок (неизвестная команда, неверный путь VFS)
set -e
cd "$(dirname "$0")/.."
echo "--- 1. Несуществующий VFS ---"
./run.sh -v vfs_data/missing.json || true
echo "--- 2. Неизвестная команда ---"
printf 'foobar\nexit\n' | ./run.sh -v vfs_data/few_files.json || true
