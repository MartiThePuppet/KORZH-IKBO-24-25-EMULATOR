"""Разбор аргументов командной строки и отладочный вывод параметров."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    vfs_path: Optional[str] = None
    script_path: Optional[str] = None
    debug: bool = False


def parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="Эмулятор оболочки ОС (вариант №12)",
    )
    parser.add_argument("-v", "--vfs", dest="vfs_path", default=None,
                        help="Путь к JSON-файлу VFS")
    parser.add_argument("-s", "--script", dest="script_path", default=None,
                        help="Путь к стартовому скрипту")
    parser.add_argument("--debug", action="store_true",
                        help="Отладочный вывод параметров")
    ns = parser.parse_args(argv)
    return Config(vfs_path=ns.vfs_path, script_path=ns.script_path, debug=ns.debug)


def dump_config(cfg: Config) -> str:
    lines = [
        f"vfs_path = {cfg.vfs_path!r}",
        f"script_path = {cfg.script_path!r}",
        f"debug = {cfg.debug}",
    ]
    return "\n".join(lines)
