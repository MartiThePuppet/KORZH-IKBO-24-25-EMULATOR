"""Виртуальная файловая система в памяти. Загружается из JSON."""
from __future__ import annotations

import base64
import json
import posixpath
from dataclasses import dataclass, field
from typing import Optional


class VfsError(Exception):
    """Ошибка загрузки/операции VFS."""


@dataclass
class Node:
    name: str
    kind: str  # "file" | "dir"
    content: str = ""
    mode: str = "644"
    children: dict[str, "Node"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        return self.kind == "dir"

    def is_file(self) -> bool:
        return self.kind == "file"


def _build(name: str, data: dict) -> Node:
    if not isinstance(data, dict):
        raise VfsError(f"Некорректный узел {name!r}: ожидался объект")
    kind = data.get("type")
    if kind == "dir":
        children_data = data.get("children", {})
        if not isinstance(children_data, dict):
            raise VfsError(f"Некорректные children у {name!r}")
        children = {n: _build(n, d) for n, d in children_data.items()}
        return Node(name=name, kind="dir", children=children)
    if kind == "file":
        if "content_base64" in data:
            try:
                content = base64.b64decode(data["content_base64"]).decode(
                    "utf-8", errors="replace"
                )
            except Exception as exc:  # noqa: BLE001
                raise VfsError(f"Некорректный base64 в {name!r}: {exc}") from exc
        else:
            content = data.get("content", "")
        return Node(
            name=name,
            kind="file",
            content=content,
            mode=str(data.get("mode", "644")),
        )
    raise VfsError(f"Неизвестный тип узла {name!r}: {kind!r}")


class Vfs:
    """Дерево в памяти + текущий каталог (список имён)."""

    def __init__(self, name: str, root: Node):
        self.name = name
        self.root = root
        self.cwd: list[str] = []  # относительный путь от root

    # ---------- загрузка ----------
    @classmethod
    def from_json_file(cls, path: str) -> "Vfs":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except FileNotFoundError as exc:
            raise VfsError(f"Файл VFS не найден: {path}") from exc
        except json.JSONDecodeError as exc:
            raise VfsError(f"Неверный JSON в VFS: {exc}") from exc
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "Vfs":
        if not isinstance(raw, dict):
            raise VfsError("Корень VFS должен быть объектом")
        name = raw.get("name", "vfs")
        root_data = raw.get("root")
        if not isinstance(root_data, dict):
            raise VfsError("Отсутствует поле 'root' или оно не объект")
        root = _build("/", root_data)
        if not root.is_dir():
            raise VfsError("Корень VFS должен быть каталогом")
        return cls(name=name, root=root)

    @classmethod
    def default(cls, name: str = "default-vfs") -> "Vfs":
        return cls(name=name, root=Node("/", "dir"))

    # ---------- навигация ----------
    def _resolve(self, path: str) -> Optional[Node]:
        """Возвращает узел по пути или None, если путь не существует."""
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
        else:
            parts = list(self.cwd) + [p for p in path.split("/") if p]

        node = self.root
        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if len(parts) > 1:
                    continue
                # упрощённо: .. от корня = корень
                continue
            if not node.is_dir() or part not in node.children:
                return None
            node = node.children[part]
        return node

    def pwd(self) -> str:
        return "/" + "/".join(self.cwd) if self.cwd else "/"

    def cwd_name(self) -> str:
        return self.cwd[-1] if self.cwd else "/"

    def list_dir(self, path: str = "") -> list[str]:
        node = self._resolve(path) if path else self._resolve(".")
        if node is None:
            raise VfsError(f"Путь не найден: {path!r}")
        if not node.is_dir():
            raise VfsError(f"Не каталог: {path!r}")
        return sorted(node.children.keys())

    def change_dir(self, path: str) -> None:
        node = self._resolve(path)
        if node is None:
            raise VfsError(f"Каталог не найден: {path!r}")
        if not node.is_dir():
            raise VfsError(f"Не каталог: {path!r}")
        if path.startswith("/"):
            self.cwd = [p for p in path.split("/") if p and p != "."]
        else:
            for part in path.split("/"):
                if not part or part == ".":
                    continue
                if part == "..":
                    if self.cwd:
                        self.cwd.pop()
                else:
                    self.cwd.append(part)
