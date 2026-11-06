"""REPL + запуск стартового скрипта.

Здесь собраны вместе:
- парсинг argv (config.py);
- загрузка VFS (vfs.py);
- цикл ввода-вывода (REPL);
- исполнение стартового скрипта (этап 2);
- маршрутизация команд (commands.py).
"""
from __future__ import annotations

import sys

from .commands import COMMANDS, CommandError
from .config import Config, dump_config, parse_args
from .parser import parse
from .vfs import Vfs, VfsError

# Шаблон приглашения. {vfs} — имя VFS, {sub} — подпуть от корня ("" или "docs/api").
PROMPT_TEMPLATE = "{vfs}:/{sub}$ "


def _prompt(vfs: Vfs) -> str:
    """Собирает строку приглашения по текущему состоянию VFS."""
    # cwd = [] → "" ; cwd = ["docs","api"] → "docs/api"
    sub = "/".join(vfs.cwd) if vfs.cwd else ""
    return PROMPT_TEMPLATE.format(vfs=vfs.name, sub=sub)


def _dispatch(line: str, vfs: Vfs | None, stub: bool) -> tuple[bool, str]:
    """Разбирает и выполняет одну строку.

    Возвращает (should_exit, output):
    - should_exit=True, если это была команда exit;
    - output — то, что надо напечатать (может быть пустым).

    Ошибки НЕ обрабатываются здесь: бросаем CommandError наверх.
    """
    tokens = parse(line)
    if not tokens:
        # Пустая строка (или строка из пробелов) — ничего не делаем.
        return False, ""
    cmd, args = tokens[0], tokens[1:]
    if cmd == "exit":
        # exit обрабатываем специально — это не функция в COMMANDS.
        return True, ""
    handler = COMMANDS.get(cmd)
    if handler is None:
        # Неизвестная команда — сигнализируем ошибкой.
        raise CommandError(f"Неизвестная команда: {cmd}")
    return False, handler(vfs, args, stub)


def _safe_run(line: str, vfs: Vfs | None, stub: bool) -> tuple[bool, str]:
    """Обёртка над _dispatch: превращает CommandError в строку "error: ...".

    Используется в REPL (где ошибка не должна завершать сессию) и в
    run_script (где ошибка должна остановить скрипт).
    """
    try:
        return _dispatch(line, vfs, stub)
    except CommandError as exc:
        # Префикс "error:" используется как признак ошибки ниже.
        return False, f"error: {exc}"


def run_script(path: str, vfs: Vfs | None, stub: bool) -> int:
    """Выполняет стартовый скрипт, останавливается на первой ошибке.

    Возвращает код возврата: 0 — успех, 1 — ошибка в скрипте,
    2 — файл скрипта не найден.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            # Читаем заранее весь файл — маленький скрипт, так проще.
            lines = fh.readlines()
    except FileNotFoundError:
        print(f"error: стартовый скрипт не найден: {path}", file=sys.stderr)
        return 2

    for raw in lines:
        # Обрезаем только \n, чтобы не терять \r на Windows (хоть и редко нужно).
        line = raw.rstrip("\n")
        # Имитируем диалог: печатаем приглашение + введённую строку.
        print(_prompt(vfs) + line)
        should_exit, out = _safe_run(line, vfs, stub)
        if out:
            print(out)
        # Признак ошибки — префикс "error:". Так скрипт останавливается
        # на первой ошибке, как требует вариант №12.
        if out.startswith("error:"):
            print(out, file=sys.stderr)
            return 1
        if should_exit:
            return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    """Главная точка входа.

    Порядок действий:
    1. Разобрать argv.
    2. Если --debug — напечатать параметры.
    3. Загрузить VFS (или создать пустую).
    4. Если задан скрипт — выполнить его и выйти.
    5. Иначе — запустить интерактивный REPL.
    """
    # argv может быть None — тогда берём sys.argv[1:]. Это удобно для тестов.
    cfg: Config = parse_args(argv if argv is not None else sys.argv[1:])

    if cfg.debug:
        print("== Параметры эмулятора ==")
        print(dump_config(cfg))
        print("==========================")

    vfs: Vfs | None = None
    if cfg.vfs_path:
        # VFS задана — пытаемся загрузить. Ошибки → stderr + код 1.
        try:
            vfs = Vfs.from_json_file(cfg.vfs_path)
        except VfsError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"VFS загружена: {vfs.name}")
    else:
        # VFS не задана — работаем с пустой VFS по умолчанию.
        vfs = Vfs.default()

    # Этап 1: без загруженной VFS команды работают как заглушки.
    # Этап 3: как только VFS загружена — работают по-настоящему.
    stub = cfg.vfs_path is None

    if cfg.script_path:
        # Неинтерактивный режим: только выполнить скрипт.
        rc = run_script(cfg.script_path, vfs, stub)
        if rc != 0:
            return rc
        return 0

    # Интерактивный REPL.
    try:
        while True:
            try:
                # input() сам напечатает приглашение и прочитает строку.
                line = input(_prompt(vfs))
            except EOFError:
                # Ctrl-D — корректный выход.
                print()
                return 0
            should_exit, out = _safe_run(line, vfs, stub)
            if out:
                # "error:" уходит в stderr, обычный вывод — в stdout.
                if out.startswith("error:"):
                    print(out, file=sys.stderr)
                else:
                    print(out)
            if should_exit:
                return 0
    except KeyboardInterrupt:
        # Ctrl-C — выходим с кодом 130 (стандартный для прерывания).
        print()
        return 130
