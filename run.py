"""Запуск эмулятора из VS Code или командной строки."""
import os
from pathlib import Path

from src.shell_emulator.cli import main


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    raise SystemExit(main())
