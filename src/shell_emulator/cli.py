"""REPL + запуск стартового скрипта."""
from __future__ import annotations

import sys

from .commands import COMMANDS, CommandError
from .config import Config, dump_config, parse_args
from .parser import parse
from .vfs import Vfs, VfsError

PROMPT_TEMPLATE = "{vfs}:/{sub}$ "


def _prompt(vfs: Vfs) -> str:
    sub = "/".join(vfs.cwd) if vfs.cwd else ""
    return PROMPT_TEMPLATE.format(vfs=vfs.name, sub=sub)


def _dispatch(line: str, vfs: Vfs | None, stub: bool) -> tuple[bool, str]:
    """Возвращает (should_exit, output)."""
    tokens = parse(line)
    if not tokens:
        return False, ""
    cmd, args = tokens[0], tokens[1:]
    if cmd == "exit":
        return True, ""
    handler = COMMANDS.get(cmd)
    if handler is None:
        raise CommandError(f"Неизвестная команда: {cmd}")
    return False, handler(vfs, args, stub)


def _safe_run(line: str, vfs: Vfs | None, stub: bool) -> tuple[bool, str]:
    try:
        return _dispatch(line, vfs, stub)
    except CommandError as exc:
        return False, f"error: {exc}"


def run_script(path: str, vfs: Vfs | None, stub: bool) -> int:
    """Выполняет стартовый скрипт, останавливается на первой ошибке."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        print(f"error: стартовый скрипт не найден: {path}", file=sys.stderr)
        return 2

    for raw in lines:
        line = raw.rstrip("\n")
        print(_prompt(vfs) + line)  # имитация диалога
        should_exit, out = _safe_run(line, vfs, stub)
        if out:
            print(out)
        if out.startswith("error:"):
            print(out, file=sys.stderr)
            return 1
        if should_exit:
            return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    cfg: Config = parse_args(argv if argv is not None else sys.argv[1:])

    if cfg.debug:
        print("== Параметры эмулятора ==")
        print(dump_config(cfg))
        print("==========================")

    vfs: Vfs | None = None
    if cfg.vfs_path:
        try:
            vfs = Vfs.from_json_file(cfg.vfs_path)
        except VfsError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"VFS загружена: {vfs.name}")
    else:
        vfs = Vfs.default()

    stub = cfg.vfs_path is None

    if cfg.script_path:
        rc = run_script(cfg.script_path, vfs, stub)
        if rc != 0:
            return rc
        return 0

    # Интерактивный REPL
    try:
        while True:
            try:
                line = input(_prompt(vfs))
            except EOFError:
                print()
                return 0
            should_exit, out = _safe_run(line, vfs, stub)
            if out:
                if out.startswith("error:"):
                    print(out, file=sys.stderr)
                else:
                    print(out)
            if should_exit:
                return 0
    except KeyboardInterrupt:
        print()
        return 130
