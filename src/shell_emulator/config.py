"""Разбор аргументов командной строки и отладочный вывод параметров.

Этап 2 требует:
- поддержать параметры -v (путь к VFS) и -s (путь к стартовому скрипту);
- вывести отладочную информацию обо всех заданных параметрах.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Все параметры запуска в одном месте.

    Optional[str] используется потому, что параметры необязательные:
    если не заданы — берутся значения по умолчанию (пустая VFS, интерактив).
    """
    vfs_path: Optional[str] = None
    script_path: Optional[str] = None
    debug: bool = False


def parse_args(argv: list[str]) -> Config:
    """Разбирает argv и возвращает Config.

    argparse сам умеет:
    - печатать --help;
    - ругаться на неизвестные флаги;
    - подставлять default.
    Нам остаётся только перенести результаты в наш Config.
    """
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="Эмулятор оболочки ОС (вариант №12)",
    )
    # -v/--vfs: путь к JSON-файлу VFS.
    parser.add_argument("-v", "--vfs", dest="vfs_path", default=None,
                        help="Путь к JSON-файлу VFS")
    # -s/--script: путь к стартовому скрипту.
    parser.add_argument("-s", "--script", dest="script_path", default=None,
                        help="Путь к стартовому скрипту")
    # --debug: включает отладочный дамп параметров.
    parser.add_argument("--debug", action="store_true",
                        help="Отладочный вывод параметров")
    ns = parser.parse_args(argv)
    return Config(vfs_path=ns.vfs_path, script_path=ns.script_path, debug=ns.debug)


def dump_config(cfg: Config) -> str:
    """Возвращает человекочитаемый дамп параметров (для --debug)."""
    # repr() показывает None как None и строки в кавычках — удобно для отладки.
    lines = [
        f"vfs_path = {cfg.vfs_path!r}",
        f"script_path = {cfg.script_path!r}",
        f"debug = {cfg.debug}",
    ]
    return "\n".join(lines)
