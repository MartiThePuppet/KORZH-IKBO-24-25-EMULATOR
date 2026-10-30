import json
import tempfile
from pathlib import Path

import pytest

from src.shell_emulator.parser import parse
from src.shell_emulator.vfs import Vfs, VfsError


def test_parse_expands_env(monkeypatch):
    monkeypatch.setenv("MYVAR", "hello")
    assert parse("echo $MYVAR ${MYVAR}") == ["echo", "hello", "hello"]


def test_vfs_loads_and_navigates():
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
    assert vfs.list_dir("/") == ["a.txt", "docs"]
    vfs.change_dir("docs")
    assert vfs.pwd() == "/docs"
    vfs.change_dir("..")
    assert vfs.pwd() == "/"


def test_vfs_bad_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(VfsError):
        Vfs.from_json_file(str(bad))
