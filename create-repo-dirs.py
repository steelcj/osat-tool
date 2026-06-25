#!/usr/bin/env python3
"""create-repo-dirs.py - create the OSAT repository directory structure under ~/bin.

Run this before git init or git clone to ensure the target directory tree exists.

Creates:
  ~/bin/
  ~/bin/<tool-name>/
  ~/bin/<tool-name>/scripts/
  ~/bin/<tool-name>/scripts/nix/
  ~/bin/<tool-name>/scripts/windows/

Usage: python3 create-repo-dirs.py <tool-name>
Example: python3 create-repo-dirs.py marp-tool
"""

from __future__ import annotations

import sys
from pathlib import Path


def log(message: str) -> None:
    print(f"[create-repo-dirs] {message}")


def fail(message: str) -> None:
    print(f"[create-repo-dirs] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    tool_name = sys.argv[1].strip()

    if not tool_name:
        fail("tool name must not be empty")

    base = Path.home() / "bin" / tool_name

    dirs = [
        Path.home() / "bin",
        base,
        base / "scripts",
        base / "scripts" / "nix",
        base / "scripts" / "windows",
    ]

    for directory in dirs:
        if directory.exists() and not directory.is_dir():
            fail(f"{directory} exists but is not a directory; inspect and remove it, then rerun")
        if directory.exists():
            log(f"exists   {directory}")
        else:
            directory.mkdir()
            log(f"created  {directory}")

    log(f"done — {base} is ready")


if __name__ == "__main__":
    main()
