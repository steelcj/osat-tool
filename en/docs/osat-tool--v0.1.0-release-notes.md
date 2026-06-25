# osat-tool v0.1.0 — Initial Release: OS-Agnostic Tool Pattern Reference Implementation

Version: 0.1.0
Status: Draft
Style Guide: style-guide--technical-documentation-for-technologists-v0.2.0.md

---

## Abstract

This document describes the initial release of `osat-tool`, a reference implementation of the versioned local binary and wrapper pattern for cross-platform command-line tools. The tool itself is intentionally trivial — it detects the current operating system and prints a confirmation message — so that the pattern is the entire subject. `osat-tool` v0.1.0 establishes the baseline for `scripts/linux/`, `scripts/macos/`, and `scripts/windows-11/` wrapper conventions, a Python installer using the standard library only, and version detection via the versioned directory name rather than a separate runtime file. It accompanies and validates `tool-installation-pattern--versioned-local-binaries-and-wrappers-v0.2.0.md`.

---

## Sources and Acknowledgements

The pattern this tool implements is documented in <a name="apa-pattern-citation"></a>[Steel (2026a)](#apa-pattern-reference). The hugo-tool installer on which `install-osat.py` is modelled is described in <a name="apa-hugo-tool-citation"></a>[Steel (2026b)](#apa-hugo-tool-reference). Authoring conventions follow the <a name="apa-styleguide-citation"></a>[style guide for technical documentation for technologists (Steel, 2026c)](#apa-styleguide-reference). Document formatting follows the <a name="apa-markdown-citation"></a>[web-ready unrendered markdown using APA 7 specification (Steel, 2026d)](#apa-markdown-reference).

---

## 1. What ships in v0.1.0

The initial release contains eleven files establishing a complete, working tool repository following the pattern.

### 1.1 The tool

`osat.py` is a single Python script requiring no external packages. It uses `platform` and `sys` from the standard library to detect the operating system name, release, version string, architecture, hostname, and Python version, and prints them in a human-readable format. It accepts `--version`, which returns the version read from the parent directory name when installed, or from the `VERSION` file when run directly from the repository. No side effects, no network calls, no file writes.

```text
osat
It's working on Linux 6.18.5
  OS version  : #1 SMP PREEMPT_DYNAMIC
  Architecture: x86_64
  Hostname    : your-hostname
  Python      : 3.12.3
```

### 1.2 The installer

`install-osat.py` is a cross-platform Python installer using the standard library only. It detects the operating system via `platform.system()`, creates the versioned directory under `~/bin/osat-tool/[version]/`, copies `osat.py` into it, selects the correct wrapper template from `scripts/[platform]/`, renders the `__OSAT_VERSION__` placeholder with the current version string, and writes the wrapper to `~/bin/osat` (Linux/macOS) or `%USERPROFILE%\bin\osat.cmd` and `osat.ps1` (Windows). It then verifies the installation by invoking the wrapper with `--version` and comparing the output against the expected version. It is idempotent — rerunning it when the current version is already installed does nothing.

The installer explicitly refuses to run as root on Linux and macOS, following the pattern established by `hugo-tool`.

### 1.3 Platform wrapper templates

Three platform directories contain the wrapper templates tracked in git:

`scripts/linux/osat` — a bash script that delegates to `$HOME/bin/osat-tool/[version]/osat.py` via `python3`. The `__OSAT_VERSION__` placeholder is replaced by the installer at render time.

`scripts/macos/osat` — identical to the Linux wrapper. macOS uses the same bash invocation. A separate file is maintained so that macOS-specific adjustments (for example, using the Homebrew Python path) can be made without affecting the Linux wrapper.

`scripts/windows-11/osat.cmd` and `scripts/windows-11/osat.ps1` — CMD and PowerShell wrappers respectively, both using `%USERPROFILE%` (CMD) or `$env:USERPROFILE` (PowerShell) to locate the versioned script. Both are rendered by the installer on Windows.

### 1.4 Repository scaffolding

`VERSION` contains `0.1.0` — the single source of version truth for the installer and for development-mode invocation of `osat.py`. `CHANGELOG.md`, `README.md`, and `ROADMAP.md` follow the conventions established by `hugo-tool` and `pagefind-tool`. `.gitignore` excludes versioned installation directories matching `[0-9]*.[0-9]*.[0-9]*/` — the same pattern used by `hugo-tool`. A `docs/` directory is present and empty, reserved for installation walkthrough documents.

---

## 2. Design decisions

### 2.1 Version from directory name

`osat.py` reads its version at runtime from `Path(__file__).resolve().parent.name` when the parent directory name matches a three-part numeric version pattern (e.g. `0.1.0`). When run directly from the repository root during development, it falls back to reading the `VERSION` file in the same directory. This eliminates the need to copy or reference a VERSION file at runtime — the versioned directory structure is itself the version record.

We considered embedding the version string as a constant in `osat.py` at install time (as some tools do via template substitution) but rejected it: it would require the installer to modify the Python source, making the versioned copy differ from the repository source in a non-obvious way. Reading from the directory name is simpler, requires no source modification, and is consistent with how the wrapper template already encodes the version.

### 2.2 Separate linux and macos wrapper files

The Linux and macOS wrapper templates are currently identical. We maintain them as separate files rather than a single `scripts/posix/` file because macOS-specific differences are likely to arise — the system Python path, Homebrew Python, or `python3` availability differs between distributions and macOS versions. Keeping the files separate from the start means a macOS-specific fix never touches the Linux wrapper.

### 2.3 Both .cmd and .ps1 on Windows

The Windows installer renders both wrapper formats. `cmd.exe` is still the default shell in many Windows terminal contexts and is used by some build tools and CI environments. PowerShell is the preferred interactive shell on Windows 11. Rendering both means the correct wrapper is available regardless of which shell invokes `osat`.

### 2.4 No docs directory content in v0.1.0

The `docs/` directory is present but empty. An installation walkthrough document — following the format of `pagefind-manual-installation-on-ubuntu-26-04-lts-v0.1.4.md` — is deferred to a subsequent patch release. The installer and README are sufficient for initial use.

---

## 3. Repository layout

```text
osat-tool/
├── .gitignore
├── CHANGELOG.md
├── README.md
├── ROADMAP.md
├── VERSION
├── docs/
├── install-osat.py
├── osat.py
└── scripts/
    ├── linux/
    │   └── osat
    ├── macos/
    │   └── osat
    └── windows-11/
        ├── osat.cmd
        └── osat.ps1
```

---

## 4. Installation

```bash
mkdir -p ~/bin
cd ~/bin
git clone https://github.com/steelcj/osat-tool.git
python3 osat-tool/install-osat.py
osat
```

Expected output on Debian 13:

```text
[osat-install] detected platform: Linux 6.x.x (x86_64)
[osat-install] tool version: 0.1.0
[osat-install] copying osat.py to /home/[user]/bin/osat-tool/0.1.0/osat.py
[osat-install] writing wrapper to /home/[user]/bin/osat
[osat-install] verifying wrapper...
[osat-install] osat 0.1.0 installed successfully via /home/[user]/bin/osat

It's working on Linux 6.x.x
  OS version  : #1 SMP PREEMPT_DYNAMIC
  Architecture: x86_64
  Hostname    : your-hostname
  Python      : 3.12.x
```

---

## 5. Commit and tag

### Initial commit example

```bash
cd ~/bin/osat-tool
```

add and commit

```bash
git add .
git commit -m "feat: initial release v0.1.0

OS-agnostic tool pattern reference implementation. Installs a cross-platform
Python script that detects and prints the current OS name, release, version,
architecture, hostname, and Python version.

Establishes:
- scripts/linux/, scripts/macos/, scripts/windows-11/ wrapper conventions
- install-osat.py: cross-platform Python installer, stdlib only
- Version detection from parent directory name at runtime
- .gitignore pattern for versioned install directories

Implements the pattern documented in:
tool-installation-pattern--versioned-local-binaries-and-wrappers-v0.2.0.md

Tested on: Linux x86_64 (Debian 13)
Pending test: macOS, Windows 11"
```

### The initial version tag

```bash
git tag -a v0.1.0 -m "v0.1.0 — Initial release

OS-agnostic tool pattern reference implementation.
See docs/ for installation walkthrough (forthcoming)."
```

Ensure for our remote and push:

```bash
git remote add origin git@github.com:steelcj/osat-tool.git
git push -u origin main --follow-tags
```

Output example:

```bash
Enumerating objects: 18, done.
Counting objects: 100% (18/18), done.
Delta compression using up to 12 threads
Compressing objects: 100% (16/16), done.
Writing objects: 100% (18/18), 10.54 KiB | 5.27 MiB/s, done.
Total 18 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
To github.com:steelcj/osat-tool.git
 * [new branch]      main -> main
 * [new tag]         v0.1.0 -> v0.1.0
branch 'main' set up to track 'origin/main'.

```



---

## Resources

### Pattern documentation
- [tool-installation-pattern--versioned-local-binaries-and-wrappers-v0.2.0.md](#apa-pattern-reference)
- [hugo-tool — reference installer implementation](#apa-hugo-tool-reference)

---

## References

<a name="apa-pattern-reference"></a>Steel, C. (2026a). *The tool installation pattern — versioned local binaries and wrappers* (Version 0.2.0) [Technical document]. https://universalcake.ca
[Return to citation](#apa-pattern-citation)

<a name="apa-hugo-tool-reference"></a>Steel, C. (2026b). *hugo-tool* [Software]. GitHub. https://github.com/steelcj/hugo-tool
[Return to citation](#apa-hugo-tool-citation)

<a name="apa-styleguide-reference"></a>Steel, C. (2026c). *Style guide: Technical documentation for technologists* (Version 0.2.0) [Technical document]. https://universalcake.ca
[Return to citation](#apa-styleguide-citation)

<a name="apa-markdown-reference"></a>Steel, C. (2026d). *Web-ready unrendered markdown using APA 7* (Version 0.2.2) [Technical document]. https://universalcake.ca
[Return to citation](#apa-markdown-citation)

---

## Changelog

| Version | Status | Notes |
|---|---|---|
| 0.1.0 | Draft | Initial release notes |
