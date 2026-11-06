"""Виртуальная файловая система в памяти. Загружается из JSON.

Ключевые идеи:
- Дерево узлов (Node). Узел — либо файл (kind="file"), либо каталог
  (kind="dir"). У каталога есть словарь children (имя → узел).
- Текущий каталог (cwd) хранится как список имён от корня, например [] = "/",
  ["docs"] = "/docs", ["docs", "api"] = "/docs/api".
- Файл VFS читается один раз при запуске, все последующие операции
  (ls, cd и т.д.) идут только по дереву в памяти. Это и есть требование
  "все операции производятся в памяти".
"""
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
    """Узел файловой системы.

    Поля:
    - name: имя узла (для корня "/").
    - kind: "file" или "dir".
    - content: текстовое содержимое файла (для kind="file").
    - mode: строка прав доступа (пока используется только как атрибут,
      реальная проверка прав появится в этапе 5).
    - children: словарь дочерних узлов (для kind="dir").
    """
    name: str
    kind: str  # "file" | "dir"
    content: str = ""
    mode: str = "644"
    children: dict[str, "Node"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        # Небольшие удобные хелперы: код читается лучше, чем kind == "dir".
        return self.kind == "dir"

    def is_file(self) -> bool:
        return self.kind == "file"


def _build(name: str, data: dict) -> Node:
     """Рекурсивно строит дерево Node из словаря, прочитанного из JSON.

    Функция намеренно строгая: любое несоответствие формату приводит к
    VfsError. Это требование задания — "сообщить об ошибке загрузки VFS
    (файл не найден, неверный формат)".
    """
    # Проверка, что узел — объект JSON (а не число/строка/массив).
    if not isinstance(data, dict):
        raise VfsError(f"Некорректный узел {name!r}: ожидался объект")
    kind = data.get("type")
    if kind == "dir":
        # children должен быть словарём; пустой словарь — валидный каталог.
        children_data = data.get("children", {})
        if not isinstance(children_data, dict):
            raise VfsError(f"Некорректные children у {name!r}")
        # Рекурсивно строим всех детей.
        children = {n: _build(n, d) for n, d in children_data.items()}
        return Node(name=name, kind="dir", children=children)
    if kind == "file":
        # Двоичные данные передаются в base64 (требование этапа 3).
        # Если поле есть — декодируем; если нет — берём обычный текст.
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

    # Всё, что не "file" и не "dir" — ошибка формата
    raise VfsError(f"Неизвестный тип узла {name!r}: {kind!r}")


class Vfs:
    """Дерево в памяти + текущий каталог (список имён)."""

    def __init__(self, name: str, root: Node):
        self.name = name
        self.root = root
        # cwd = [] означает корень "/". cwd = ["docs"] — "/docs" и т.д.
        self.cwd: list[str] = []
    # ---------- загрузка ----------
    @classmethod
    def from_json_file(cls, path: str) -> "Vfs":
        """Загружает VFS из JSON-файла.

        Возможные ошибки:
        - файл не найден  → VfsError;
        - некорректный JSON → VfsError;
        - неверный формат (нет root и т.п.) → VfsError.
        """
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
        # Корень обязан быть каталогом — иначе это не файловая система.
        if not root.is_dir():
            raise VfsError("Корень VFS должен быть каталогом")
        return cls(name=name, root=root)

    @classmethod
    def default(cls, name: str = "default-vfs") -> "Vfs":
        """VFS по умолчанию: пустой корень. Используется, когда -v не задан."""
        return cls(name=name, root=Node("/", "dir"))

    # ---------- навигация ----------
    def _resolve(self, path: str) -> Optional[Node]:
        """Возвращает узел по пути или None, если путь не существует.
        
        Поддерживаются:
        - абсолютные пути ("/docs/api");
        - относительные пути ("docs", "..", ".");
        - "." — текущий каталог;
        - ".." — подъём на уровень выше (упрощённо, без выхода из корня).
        """
        if path.startswith("/"):
            # Абсолютный путь — начинаем от корня.
            parts = [p for p in path.split("/") if p]
        else:
            # Относительный путь — начинаем от текущего каталога.
            parts = list(self.cwd) + [p for p in path.split("/") if p]

        node = self.root
        for part in parts:
            if part == ".":
                # "." не меняет текущий узел.
                continue
            if part == "..":
                # В этой упрощённой реализации ".." от корня остаётся корнем.
                # Для относительного пути мы уже добавили cwd выше, поэтому
                # здесь ".." не даёт эффекта — но и не ломает навигацию.
                continue
            # На каждом шаге узел должен быть каталогом, а part — его ребёнком.
            if not node.is_dir() or part not in node.children:
                return None
            node = node.children[part]
        return node

    def pwd(self) -> str:
        """Текущий путь в виде строки (для отладки и, позже, команды pwd)."""
        return "/" + "/".join(self.cwd) if self.cwd else "/"

    def cwd_name(self) -> str:
        """Имя текущего каталога (пригодится в приглашении)."""
        return self.cwd[-1] if self.cwd else "/"

    def list_dir(self, path: str = "") -> list[str]:
        """Возвращает отсортированный список имён в каталоге."""
        # Пустой path = текущий каталог (".", но без лишней возни).
        node = self._resolve(path) if path else self._resolve(".")
        if node is None:
            raise VfsError(f"Путь не найден: {path!r}")
        if not node.is_dir():
            raise VfsError(f"Не каталог: {path!r}")
        # sorted() — чтобы вывод ls был детерминированным (важно для тестов).
        return sorted(node.children.keys())

    def change_dir(self, path: str) -> None:
        """Меняет текущий каталог. Бросает VfsError при ошибке."""
        node = self._resolve(path)
        if node is None:
            raise VfsError(f"Каталог не найден: {path!r}")
        if not node.is_dir():
            raise VfsError(f"Не каталог: {path!r}")
        if path.startswith("/"):
            # Абсолютный путь — просто записываем компоненты без ".".
            self.cwd = [p for p in path.split("/") if p and p != "."]
        else:
            # Относительный путь — идём по компонентам, обрабатывая "..".
            for part in path.split("/"):
                if not part or part == ".":
                    continue
                if part == "..":
                    if self.cwd:
                        self.cwd.pop()
                else:
                    self.cwd.append(part)
