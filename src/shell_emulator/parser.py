"""Парсер команд: разделение по пробелам + раскрытие переменных окружения."""
import os
import re

_ENV_RE = re.compile(r"\$(\w+|\{[^}]+\})")


def expand_env(token: str) -> str:
    """Раскрывает $VAR и ${VAR} через окружение реальной ОС.

    Неизвестные переменные заменяются на пустую строку (как в sh).
    """

    def _sub(match: re.Match) -> str:
        name = match.group(1)
        if name.startswith("{") and name.endswith("}"):
            name = name[1:-1]
        return os.environ.get(name, "")

    return _ENV_RE.sub(_sub, token)


def parse(line: str) -> list[str]:
    """Разбивает строку на токены по пробелам и раскрывает env-переменные."""
    tokens = line.strip().split()
    return [expand_env(t) for t in tokens]
