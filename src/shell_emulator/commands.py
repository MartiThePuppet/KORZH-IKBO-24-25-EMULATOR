"""Реализация команд REPL. На этапе 1: ls, cd — заглушки; на этапе 3: реальные."""
from __future__ import annotations

from .vfs import Vfs, VfsError


class CommandError(Exception):
    """Ошибка выполнения команды."""


def cmd_ls(vfs: Vfs | None, args: list[str], stub: bool) -> str:
    if stub or vfs is None:
        return "ls: " + " ".join(args)
    target = args[0] if args else "."
    try:
        names = vfs.list_dir(target)
    except VfsError as exc:
        raise CommandError(str(exc)) from exc
    if not names:
        return ""
    return "\n".join(names)


def cmd_cd(vfs: Vfs | None, args: list[str], stub: bool) -> str:
    if stub or vfs is None:
        return "cd: " + " ".join(args)
    if len(args) != 1:
        raise CommandError("cd: требуется один аргумент")
    try:
        vfs.change_dir(args[0])
    except VfsError as exc:
        raise CommandError(str(exc)) from exc
    return ""


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
}
