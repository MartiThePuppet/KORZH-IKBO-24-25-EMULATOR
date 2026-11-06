#!/usr/bin/env bash
# Тест обработки ошибок: несуществующий VFS и неизвестная команда.
set -e
cd "$(dirname "$0")/.."

echo "--- 1. Несуществующий VFS ---"
# Ожидаем "error: Файл VFS не найден: ..." и код 1.
# `|| true` не даёт set -e уронить весь скрипт — ошибка ожидаемая.
./run.sh -v vfs_data/missing.json || true

echo "--- 2. Неизвестная команда ---"
# Ожидаем "error: Неизвестная команда: foobar" в stderr.
printf 'foobar\nexit\n' | ./run.sh -v vfs_data/few_files.json || true
