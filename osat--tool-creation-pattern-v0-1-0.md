# OSAT — Tool Creation Pattern

Version: 0.1.0
Status: Draft
Style Guide: style-guide--technical-documentation-for-technologists-v0.2.0

## Abstract

This document captures the OS-Agnostic Tool (OSAT) pattern as implemented across hugo-tool, rclone-tool, pagefind-tool, and osat-tool. It exists so that new tools following this pattern can be produced quickly and consistently, and so that the pattern itself can be refined over time without losing the decisions and rationale behind its current form.

## 1. What the pattern is

An OSAT is a self-contained, user-local binary installer and wrapper. It installs a tool for the invoking user without requiring elevated privileges, pins versions side by side to allow rollback, and renders a platform-appropriate wrapper so the installed version runs from anywhere on PATH. The installer is a single Python 3 script using only the standard library. No virtualenv, no pip, no package manager.

The pattern has three stable properties. First, it is idempotent: rerunning the installer does nothing if the latest version is already active, and otherwise installs the new version alongside the existing ones without removing them. Second, it is sovereign: it has no runtime dependencies beyond Python 3.8 or later and network access to the tool's release host. Third, it is auditable: every install verifies the downloaded artefact against the publisher's published checksum before touching the filesystem.

## 2. Repository layout

Every OSAT repository follows this layout:

```
<tool-name>/
├── .gitignore              maintained by the installer; excludes versioned binary dirs
├── README.md               install, upgrade, rollback, layout sections
├── ROADMAP.md              planned platform bringup and known gaps
├── install-<tool-name>.py  the installer
├── scripts/
│   ├── nix/
│   │   └── <tool-name>     nix wrapper template (shell)
│   └── windows/            Windows wrapper templates (.cmd and .ps1) if supported
└── <version>/              created by the installer; git-ignored
    └── <binary>
```

The versioned binary directories are excluded from git by a pattern like `[0-9]*.[0-9]*.[0-9]*/` which the installer adds to `.gitignore` on first run if it is not already present.

## 3. Install layout on disk

The installer writes to the user's home directory only. It never touches system paths.

```
~/bin/<tool-name>                    wrapper (rendered by installer from scripts/nix/<tool-name>)
~/bin/<tool-name>/                   the cloned repository lives here
~/bin/<tool-name>/<version>/<binary> installed binary, versioned side by side
```

The convention is to clone the repository into `~/bin/<tool-name>/` so the wrapper at `~/bin/<tool-name>` and the repository at `~/bin/<tool-name>/` coexist. The `.gitignore` excludes the versioned subdirectories. The wrapper is a sibling of the repository directory, not inside it.

## 4. The installer script

### 4.1 Structure

The installer follows a consistent internal structure across all tools:

```python
#!/usr/bin/env python3
"""Docstring: what it does, layout, supported platforms, requirements, usage."""

from __future__ import annotations
# standard library imports only

# Constants: API_URL, RELEASE_BASE, USER_AGENT, directory paths, ASSET_PLATFORMS dict
# Helper functions: log(), fail()
# Core functions: detect_asset_platform(), fetch(), latest_version(),
#                 expected_checksum(), binary_ok(), render_wrapper(),
#                 ensure_gitignore(), install_binary(), install_wrapper(),
#                 post_install_notes()
# Entry point: main()

if __name__ == "__main__":
    main()
```

### 4.2 Platform detection

The `ASSET_PLATFORMS` dict maps `(platform.system(), platform.machine())` tuples to the release asset platform segment used in the tool's release filenames. Any unlisted combination calls `fail()` with an explicit message directing to `ROADMAP.md`.

```python
ASSET_PLATFORMS = {
    ("Linux", "x86_64"):  "linux-amd64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Darwin", "x86_64"): "darwin-universal",
    ("Darwin", "arm64"):  "darwin-universal",
}
```

Extend this dict as platforms are validated and added. Do not silently fall back to a guess — unsupported platforms must fail loudly.

### 4.3 Version detection

We query the GitHub Releases API for the latest stable release tag and strip the leading `v`:

```python
API_URL = "https://api.github.com/repos/<org>/<repo>/releases/latest"

def latest_version() -> str:
    release = json.loads(fetch(API_URL))
    tag = release.get("tag_name", "")
    if not tag.startswith("v") or len(tag) < 2:
        fail(f"unexpected tag_name in API response: {tag!r}")
    return tag[1:]
```

For tools that do not use the GitHub Releases API (e.g. tools that publish checksums at a custom URL), adapt this function but keep the same contract: return a bare version string like `1.2.3`.

### 4.4 Checksum verification

After downloading the release artefact, we fetch the publisher's checksums file and verify the SHA-256 digest before touching the filesystem. If verification fails, we call `fail()` — we do not install.

```python
def expected_checksum(checksums_text: str, asset_name: str) -> str:
    for line in checksums_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == asset_name:
            return parts[0]
    fail(f"{asset_name} is not listed in the published checksums file")

# In install_binary():
expected = expected_checksum(checksums_text, asset_name)
actual = hashlib.sha256(asset_bytes).hexdigest()
if actual != expected:
    fail("checksum verification failed; do not install this artefact")
```

The checksums file format assumed here is the standard two-column `<hash>  <filename>` format used by Hugo, rclone, and most Go-distributed tools. If the tool uses a different format, adapt `expected_checksum()` but keep the same verification contract.

### 4.5 Binary health check

After installation, we verify the binary reports the expected version. This catches silent corruption and mismatched wrappers.

```python
def binary_ok(binary_path: Path, version: str) -> bool:
    if not (binary_path.is_file() and os.access(binary_path, os.X_OK)):
        return False
    try:
        result = subprocess.run(
            [str(binary_path), "version"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and f"v{version}" in result.stdout
```

Not all tools use `version` as their version subcommand. Use `--version` or `-v` as appropriate, and adapt the version string search to match the tool's output format.

### 4.6 Wrapper rendering

The wrapper is a shell script template stored in `scripts/nix/<tool-name>`. It contains a `__TOOL_VERSION__` placeholder (named after the tool) that the installer replaces with the active version string at install time.

```python
TEMPLATE_PATH = REPO_DIR / "scripts" / "nix" / "<tool-name>"

def render_wrapper(version: str) -> str:
    if not TEMPLATE_PATH.is_file():
        fail(f"wrapper template not found at {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if "__TOOL_VERSION__" not in template:
        fail(f"{TEMPLATE_PATH} does not contain the __TOOL_VERSION__ placeholder")
    return template.replace("__TOOL_VERSION__", version)
```

A typical nix wrapper template:

```bash
#!/bin/sh
TOOL_BIN="$HOME/bin/<tool-name>/__TOOL_VERSION__/<tool-name>"
exec "$TOOL_BIN" "$@"
```

### 4.7 Idempotency check

The installer checks whether the binary for the latest version is already present and the rendered wrapper content already matches. If both are true, it exits early with a "nothing to do" message.

```python
binary_current = binary_ok(binary_path, version)
wrapper_current = (
    WRAPPER_PATH.is_file()
    and WRAPPER_PATH.read_text(encoding="utf-8") == wrapper_content
)

if binary_current and wrapper_current:
    log(f"<tool-name> v{version} is already installed and active; nothing to do")
    return
```

### 4.8 Root guard

The installer refuses to run as root. User-local installs should not require sudo, and running as root would write to `/root/bin` rather than the invoking user's home directory.

```python
if hasattr(os, "geteuid") and os.geteuid() == 0:
    fail("this script installs to the invoking user's home directory; do not run with sudo")
```

### 4.9 Post-install notes

After a successful install, the installer checks whether `~/bin` is on the current PATH and warns if not. It also warns if another installation of the tool (e.g. from a system package manager) is shadowing the wrapper.

```python
def post_install_notes() -> None:
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if str(BIN_DIR) not in path_dirs:
        log(f"NOTE: {BIN_DIR} is not in the current PATH; ...")
    resolved = shutil.which("<tool-name>")
    if resolved and Path(resolved) != WRAPPER_PATH:
        log(f"WARNING: the shell currently resolves <tool-name> to {resolved}; ...")
```

## 5. The nix wrapper template

The wrapper template is a plain shell script. It is the only file in `scripts/nix/`. It must be committed without a file extension so it renders as an executable shell script on install.

```bash
#!/bin/sh
# <tool-name> — rendered by install-<tool-name>.py; do not edit by hand
TOOL_BIN="$HOME/bin/<tool-name>/__TOOL_VERSION__/<tool-name>"
exec "$TOOL_BIN" "$@"
```

The rendered copy at `~/bin/<tool-name>` is executable. The template in the repository does not need to be executable; the installer sets permissions on the rendered copy.

## 6. Windows support

Windows support is added to the repository layout when it is validated, not speculatively. Until then, it appears in `ROADMAP.md` only. When added, the `scripts/windows/` directory contains two files: `<tool-name>.cmd` for `cmd.exe` and `<tool-name>.ps1` for PowerShell. The installer detects `platform.system() == "Windows"` and renders the appropriate wrapper.

We observed in rclone-tool that Windows binary installation works before wrapper rendering is fully solved. The ROADMAP is the right place to track the gap. Do not ship a Windows wrapper that has not been tested.

## 7. README structure

Every OSAT README follows this section order. Do not add sections or reorder them.

```markdown
# <tool-name>

## Description
## Requirements
## Install
## Upgrade
## Rollback
## Layout
## See also   (optional; link to related tools and upstream docs)
```

The Install section always shows the four-line clone-and-run sequence. The Upgrade section always shows the pull-and-rerun sequence. The Rollback section always explains the side-by-side layout and how to edit the wrapper. The Layout section always shows the directory tree.

## 8. ROADMAP.md

`ROADMAP.md` documents planned work that is not yet implemented. It is not a backlog — it is a statement of known gaps and their planned resolution. Each entry names the platform or capability, the current status, and the next step.

A new tool's ROADMAP at creation should at minimum document Windows bringup if Windows wrappers are not yet present, and any architectures listed in `ASSET_PLATFORMS` as planned but not yet validated.

## 9. Decisions and rationale

### 9.1 Why stdlib only

We chose Python standard library only because it eliminates the need for a virtualenv, pip, or any package installation step before the installer can run. The installer is the first thing a user runs in a fresh environment. It must have no prerequisites beyond Python 3.8 itself. Every dependency added to the installer adds a failure mode before the tool is even installed.

We considered using `requests` for HTTP and `packaging` for version comparison. Both would simplify the code. We rejected both because they require a prior install step, which defeats the purpose of a zero-prerequisite installer.

### 9.2 Why side-by-side versioning

We keep installed versions side by side under `~/bin/<tool-name>/<version>/` rather than overwriting a single installation. This allows rollback without a reinstall. It also means the installer can verify a new version is healthy before repointing the wrapper, and can leave the previous version intact if verification fails.

We considered managing a single `current` symlink. We rejected it because symlinks behave differently on Windows and introduce a layer of indirection that complicates the wrapper template and the health check.

### 9.3 Why a rendered wrapper rather than a symlink

The wrapper is a rendered shell script rather than a symlink to the binary. This allows the wrapper to be extended later (e.g. to set environment variables, inject config paths, or add platform-specific adjustments) without changing the binary or the installer logic. The wrapper template is version-controlled; the rendered copy is not.

We considered a simple symlink. We rejected it because symlinks do not work uniformly across platforms (particularly Windows), and because a rendered wrapper is more transparent — a user can read `~/bin/<tool-name>` and understand exactly what it does.

### 9.4 Why GitHub Releases API rather than version files

We query the GitHub Releases API for the latest stable version rather than maintaining a pinned version in the repository. This means the installer always installs the latest stable release without requiring a manual version bump in the repository. The installer is the source of truth for what version is current.

We considered a `VERSION` file in the repository (as osat-tool uses for its own version). For tools that distribute their binaries via GitHub Releases, the API is more reliable than a manually maintained file. For the tool's own version (distinct from the binary being installed), a `VERSION` file remains appropriate.

## 10. Creating a new OSAT

To create a new OSAT for a tool named `<tool-name>`:

1. Create the repository as `<tool-name>-tool` following the layout in section 2.
2. Copy `install-hugo.py` or `install-rclone.py` as the starting point. Choose hugo-tool if the tool distributes `.tar.gz` archives; rclone-tool if it distributes `.zip` archives or has a wider platform matrix.
3. Replace all tool-specific constants: `API_URL`, `RELEASE_BASE`, `ASSET_PLATFORMS`, path constants, and the placeholder name in `render_wrapper()`.
4. Adapt `install_binary()` for the archive format and the location of the binary within the archive.
5. Adapt `binary_ok()` for the tool's version command and output format.
6. Write the wrapper template in `scripts/nix/<tool-name>`.
7. Write `README.md` and `ROADMAP.md` following section 7 and section 8.
8. Run the installer. Verify `<tool-name> version` works. Verify rerunning does nothing. Verify the wrapper content matches the template with the version substituted.

## License

This document, *OSAT — Tool Creation Pattern*, by **Christopher Steel**, with AI assistance from **Claude Sonnet 4.6 (Anthropic)**, is licensed under the [GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | Initial draft derived from hugo-tool, rclone-tool, osat-tool, pagefind-tool |
