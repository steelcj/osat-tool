#!/usr/bin/env python3
"""osat — OS-agnostic tool pattern test.

Detects the operating system name, release, version, and architecture,
and prints a human-readable confirmation that the tool is working.

Standard library only. No external packages required.
Python 3.8+.

Usage:
    osat
    osat --version
"""
from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path


def read_tool_version() -> str:
    # When installed, osat.py lives at ~/bin/osat-tool/<version>/osat.py.
    # The version is the parent directory name — no separate VERSION file needed
    # at runtime. Fall back to reading VERSION from the repo root if running
    # directly from the repository (e.g. during development).
    parent_name = Path(__file__).resolve().parent.name
    # Check if parent name looks like a version number (e.g. 0.1.0)
    parts = parent_name.split(".")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return parent_name
    version_file = Path(__file__).resolve().parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OS-agnostic tool pattern test — prints OS detection output."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the tool version and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(read_tool_version())
        sys.exit(0)

    system   = platform.system()
    release  = platform.release()
    version  = platform.version()
    machine  = platform.machine()
    node     = platform.node()
    py_ver   = sys.version.split()[0]

    print(f"It's working on {system} {release}")
    print(f"  OS version  : {version}")
    print(f"  Architecture: {machine}")
    print(f"  Hostname    : {node}")
    print(f"  Python      : {py_ver}")


if __name__ == "__main__":
    main()
