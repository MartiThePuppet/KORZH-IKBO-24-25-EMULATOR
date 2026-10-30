#!/usr/bin/env bash
# Тест: запуск без VFS (VFS по умолчанию, команды-заглушки)
set -e
cd "$(dirname "$0")/.."
printf 'ls\ncd /\nexit\n' | ./run.sh
