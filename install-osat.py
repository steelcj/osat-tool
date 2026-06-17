#!/usr/bin/env python3
"""install-osat.py — install osat for the current user.

Copies osat.py into a versioned directory under ~/bin/osat-tool/ and renders
the correct wrapper script for the current platform at ~/bin/osat (Linux/macOS)
or %USERPROFILE%\\bin\\osat.cmd and osat.ps1 (Windows).

Layout after installation:

  ~/bin/osat                           rendered bash wrapper (Linux/macOS)
  ~/bin/osat-tool/<version>/osat.py   versioned copy of the tool
  ~/bin/osat-tool/                    this repository (cloned here)

  %USERPROFILE%\\bin\\osat.cmd          rendered CMD wrapper (Windows)
  %USERPROFILE%\\bin\\osat.ps1          rendered PowerShell wrapper (Windows)
  %USERPROFILE%\\bin\\osat-tool\\<v>\\   versioned copy (Windows)

Supported platforms:
  Linux   (x86_64, aarch64)
  macOS   (x86_64, arm64)
  Windows 11 (x86_64) — renders .cmd and .ps1 wrappers

Requires only the Python standard library (Python 3.8+).

Usage:
    python3 install-osat.py
"""
from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path


REPO_DIR     = Path(__file__).resolve().parent
VERSION_FILE = REPO_DIR / "VERSION"
TOOL_SCRIPT  = REPO_DIR / "osat.py"

SCRIPTS = {
    "Linux":   REPO_DIR / "scripts" / "linux"   / "osat",
    "Darwin":  REPO_DIR / "scripts" / "macos"   / "osat",
    "Windows": {
        "cmd": REPO_DIR / "scripts" / "windows-11" / "osat.cmd",
        "ps1": REPO_DIR / "scripts" / "windows-11" / "osat.ps1",
    },
}

PLACEHOLDER = "__OSAT_VERSION__"

SUPPORTED_SYSTEMS = {"Linux", "Darwin", "Windows"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    print(f"[osat-install] {message}")


def fail(message: str) -> None:
    print(f"[osat-install] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def bin_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", Path.home())) / "bin"
    return Path.home() / "bin"


def tool_dir() -> Path:
    return bin_dir() / "osat-tool"


def read_version() -> str:
    if not VERSION_FILE.is_file():
        fail(f"VERSION file not found at {VERSION_FILE}")
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        fail("VERSION file is empty")
    return version


def render_template(template_path: Path, version: str) -> str:
    if not template_path.is_file():
        fail(f"wrapper template not found at {template_path}")
    content = template_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in content:
        fail(f"{template_path} does not contain the {PLACEHOLDER} placeholder")
    return content.replace(PLACEHOLDER, version)


def make_executable(path: Path) -> None:
    path.chmod(
        stat.S_IRWXU
        | stat.S_IRGRP | stat.S_IXGRP
        | stat.S_IROTH | stat.S_IXOTH
    )


def verify(wrapper: Path, version: str) -> bool:
    try:
        result = subprocess.run(
            [str(wrapper), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return result.returncode == 0 and version in result.stdout.strip()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Installation steps
# ---------------------------------------------------------------------------

def install_tool_script(version: str) -> Path:
    versioned_dir = tool_dir() / version
    versioned_dir.mkdir(parents=True, exist_ok=True)
    dest = versioned_dir / "osat.py"
    log(f"copying osat.py to {dest}")
    shutil.copyfile(TOOL_SCRIPT, dest)
    make_executable(dest)
    return dest


def install_wrapper_linux_macos(version: str, system: str) -> Path:
    template_path = SCRIPTS[system]
    content = render_template(template_path, version)
    wrapper = bin_dir() / "osat"
    bin_dir().mkdir(parents=True, exist_ok=True)
    log(f"writing wrapper to {wrapper}")
    wrapper.write_text(content, encoding="utf-8")
    make_executable(wrapper)
    return wrapper


def install_wrapper_windows(version: str) -> tuple[Path, Path]:
    cmd_content = render_template(SCRIPTS["Windows"]["cmd"], version)
    ps1_content = render_template(SCRIPTS["Windows"]["ps1"], version)
    bd = bin_dir()
    bd.mkdir(parents=True, exist_ok=True)
    cmd_wrapper = bd / "osat.cmd"
    ps1_wrapper = bd / "osat.ps1"
    log(f"writing CMD wrapper to {cmd_wrapper}")
    cmd_wrapper.write_text(cmd_content, encoding="utf-8")
    log(f"writing PowerShell wrapper to {ps1_wrapper}")
    ps1_wrapper.write_text(ps1_content, encoding="utf-8")
    return cmd_wrapper, ps1_wrapper


def post_install_notes(wrapper: Path) -> None:
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    bd = str(bin_dir())
    if bd not in path_dirs:
        if platform.system() == "Windows":
            log(
                f"NOTE: {bd} is not in PATH. Add it via System Properties > "
                f"Environment Variables, or run in PowerShell: "
                f'$env:PATH = "{bd};" + $env:PATH'
            )
        else:
            log(
                f"NOTE: {bd} is not in PATH. On Debian/Ubuntu, ~/.profile adds "
                f"~/bin automatically at next login if the directory exists, or run: "
                f'export PATH="{bd}:$PATH"'
            )

    if platform.system() != "Windows":
        resolved = shutil.which("osat")
        if resolved and Path(resolved) != wrapper:
            log(
                f"WARNING: shell currently resolves 'osat' to {resolved}; "
                f"adjust PATH so {wrapper} takes precedence"
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    system = platform.system()

    if system not in SUPPORTED_SYSTEMS:
        fail(
            f"platform '{system}' ({platform.machine()}) is not yet supported; "
            f"see ROADMAP.md for planned platform bringup"
        )

    if system != "Windows":
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            fail(
                "this script installs to the invoking user's home directory; "
                "do not run with sudo"
            )

    log(f"detected platform: {system} {platform.release()} ({platform.machine()})")

    version = read_version()
    log(f"tool version: {version}")

    versioned_script = tool_dir() / version / "osat.py"
    script_current   = versioned_script.is_file()

    if system == "Windows":
        bd           = bin_dir()
        cmd_wrapper  = bd / "osat.cmd"
        ps1_wrapper  = bd / "osat.ps1"
        wrapper_current = cmd_wrapper.is_file() and ps1_wrapper.is_file()

        if script_current and wrapper_current:
            log(f"osat {version} is already installed and active; nothing to do")
            return

        if not script_current:
            install_tool_script(version)
        else:
            log(f"osat.py {version} already present at {versioned_script}")

        install_wrapper_windows(version)
        log("verifying CMD wrapper...")
        if verify(cmd_wrapper, version):
            log(f"osat {version} installed successfully via {cmd_wrapper}")
        else:
            fail(f"CMD wrapper verification failed for {cmd_wrapper}")
        post_install_notes(cmd_wrapper)

    else:
        wrapper       = bin_dir() / "osat"
        template_path = SCRIPTS[system]
        wrapper_content = render_template(template_path, version)
        wrapper_current = (
            wrapper.is_file()
            and wrapper.read_text(encoding="utf-8") == wrapper_content
        )

        if script_current and wrapper_current:
            log(f"osat {version} is already installed and active; nothing to do")
            return

        if not script_current:
            install_tool_script(version)
        else:
            log(f"osat.py {version} already present at {versioned_script}; updating wrapper only")

        install_wrapper_linux_macos(version, system)

        log("verifying wrapper...")
        if verify(wrapper, version):
            log(f"osat {version} installed successfully via {wrapper}")
        else:
            fail(f"wrapper verification failed for {wrapper}")

        post_install_notes(wrapper)


if __name__ == "__main__":
    main()
