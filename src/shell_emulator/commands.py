"""Реализация команд REPL. 

На этапе 1 ls/cd — заглушки, которые печатают своё имя и аргументы.
После подключения VFS (этап 3) те же функции начинают работать с реальным
деревом. Флаг `stub` позволяет одной и той же команде вести себя по-разному
в зависимости от того, загружена ли VFS.
"""
from __future__ import annotations

from .vfs import Vfs, VfsError


class CommandError(Exception):
    """Ошибка выполнения команды.
    
    Отдельный тип исключения нужен, чтобы CLI мог напечатать сообщение
    в stderr и не путать такие ошибки с багами в самом эмуляторе.
    """


def cmd_ls(vfs: Vfs | None, args: list[str], stub: bool) -> str:
    """ls [path] — вывести содержимое каталога.

    В режиме заглушки (stub=True или VFS не загружена) просто эхом
    возвращает имя команды и аргументы — так требует этап 1.
    """
    if stub or vfs is None:
        # Этап 1: заглушка. "ls: a b c" в stdout.
        return "ls: " + " ".join(args)
    # Этап 3: реальная логика — читаем каталог из дерева VFS.
    target = args[0] if args else "."
    try:
        names = vfs.list_dir(target)
    except VfsError as exc:
        # VfsError → CommandError: CLI умеет обрабатывать только CommandError.
        raise CommandError(str(exc)) from exc
     # Пустой каталог → пустая строка (никакого вывода).
    if not names:
        return ""
    # Каждое имя с новой строки, как в настоящем ls.
    return "\n".join(names)


def cmd_cd(vfs: Vfs | None, args: list[str], stub: bool) -> str:
    """cd <path> — сменить текущий каталог.

    В режиме заглушки эхом возвращает имя и аргументы.
    В реальном режиме: ровно один аргумент, путь существует и это каталог.
    """
    if stub or vfs is None:
        return "cd: " + " ".join(args)
    if len(args) != 1:
        # cd без аргумента или с несколькими — ошибка (для простоты).
        raise CommandError("cd: требуется один аргумент")
    try:
        vfs.change_dir(args[0])
    except VfsError as exc:
        raise CommandError(str(exc)) from exc
    # cd ничего не печатает при успехе.
    return ""


# Реестр команд: имя → функция. Именно сюда заглядывает CLI, когда
# разбирает первую строку ввода. Новые команды на следующих этапах
# просто добавляются в этот словарь.
COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
}
