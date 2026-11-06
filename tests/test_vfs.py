"""Базовые тесты VFS и парсера.

Покрываем три вещи:
- раскрытие env-переменных в парсере;
- навигацию по VFS (load, ls, cd, ..);
- обработку ошибок загрузки (битый JSON).
"""
import json
import tempfile
from pathlib import Path

import pytest

# Импортируем модули из src/. Если pytest запускается из корня репозитория,
# а корень содержит src/ — эти импорты работают без установки пакета.
from src.shell_emulator.parser import parse
from src.shell_emulator.vfs import Vfs, VfsError


def test_parse_expands_env(monkeypatch):
    """$VAR и ${VAR} должны подставляться из окружения."""
    # monkeypatch.setenv — безопасная установка переменной на время теста.
    monkeypatch.setenv("MYVAR", "hello")
    assert parse("echo $MYVAR ${MYVAR}") == ["echo", "hello", "hello"]


def test_vfs_loads_and_navigates():
    """Проверяем ls/cd/.. на маленьком дереве."""
    raw = {
        "name": "t",
        "root": {
            "type": "dir",
            "children": {
                "a.txt": {"type": "file", "content": "x"},
                "docs": {"type": "dir", "children": {}},
            },
        },
    }
    vfs = Vfs.from_dict(raw)
    # ls / → ["a.txt", "docs"] (отсортировано).
    assert vfs.list_dir("/") == ["a.txt", "docs"]
    # cd docs → cwd = /docs
    vfs.change_dir("docs")
    assert vfs.pwd() == "/docs"
    # cd .. → cwd = /
    vfs.change_dir("..")
    assert vfs.pwd() == "/"


def test_vfs_bad_json(tmp_path: Path):
    """Битый JSON должен приводить к VfsError, а не к падению."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(VfsError):
        Vfs.from_json_file(str(bad))
