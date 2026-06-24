#!/usr/bin/env python3
"""create-repo-dirs.py - create the marp-tool repository directory structure under ~/bin.

Run this before git init or git clone to ensure the target directory tree exists.

Creates:
  ~/bin/
  ~/bin/marp-tool/
  ~/bin/marp-tool/scripts/
  ~/bin/marp-tool/scripts/nix/
  ~/bin/marp-tool/scripts/windows/

Usage: python3 create-repo-dirs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

DIRS = [
    Path.home() / "bin",
    Path.home() / "bin" / "marp-tool",
    Path.home() / "bin" / "marp-tool" / "scripts",
    Path.home() / "bin" / "marp-tool" / "scripts" / "nix",
    Path.home() / "bin" / "marp-tool" / "scripts" / "windows",
]


def log(message: str) -> None:
    print(f"[create-repo-dirs] {message}")


def fail(message: str) -> None:
    print(f"[create-repo-dirs] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    for directory in DIRS:
        if directory.exists() and not directory.is_dir():
            fail(f"{directory} exists but is not a directory; inspect and remove it, then rerun")
        if directory.exists():
            log(f"exists   {directory}")
        else:
            directory.mkdir()
            log(f"created  {directory}")

    log("done — directory structure is ready")


if __name__ == "__main__":
    main()
