# osat-tool

## Description

OS-agnostic tool pattern test. Installs a cross-platform Python script that detects the current operating system and prints a human-readable confirmation. The tool itself is trivial — the value is the installation pattern it demonstrates.

This repository is a reference implementation of the versioned local binary and wrapper pattern described in `tool-installation-pattern--versioned-local-binaries-and-wrappers-for-nix-v0.1.0.md`.

## What it does

```
osat
```

Output on Linux:

```
It's working on Linux 6.8.0-47-generic
  OS version  : #47-Ubuntu SMP PREEMPT_DYNAMIC Fri Sep 27 21:40:26 UTC 2024
  Architecture: x86_64
  Hostname    : your-hostname
  Python      : 3.12.3
```

## Requirements

- Python 3.8 or later (standard library only — no packages to install)
- Linux, macOS, or Windows 11
- `~/bin` on PATH (Linux/macOS) or `%USERPROFILE%\bin` on PATH (Windows)

## Install

```
mkdir -p ~/bin
cd ~/bin
git clone https://github.com/steelcj/osat-tool.git
python3 osat-tool/install-osat.py
osat
```

If `osat` is not found, open a new terminal — `~/bin` joins PATH at next login on Debian/Ubuntu if the directory exists.

## Upgrade

Increment the version in `VERSION`, then rerun the installer:

```
python3 ~/bin/osat-tool/install-osat.py
```

The installer detects the new version, installs it alongside the existing version, and repoints the wrapper.

## Rollback

Installed versions are kept side by side under `~/bin/osat-tool/<version>/`. To roll back, edit the version path in `~/bin/osat` to a previously installed version.

## Layout

```
~/bin/osat                          rendered wrapper (selects active version)
~/bin/osat-tool/                    this repository
~/bin/osat-tool/<version>/osat.py   versioned copy of the tool script
```

Versioned directories are excluded from git by `.gitignore`.

## Creating Custom OS Agnostic Installers

### Reference Docs

See `en/docs` for addition information on [software-installation-archetypes](./en/docs/software-installation-archetypes.md) as well as some examples on other approaches to OS Agnostic installers in the wild.

Using similar patterns you can create your own OSAT installers. Any tools for doing this will be collected in this repository

Example:

create-repo-dirs.py can be modified so you can pass your tool name and build the structure for a custom osat tool installerS





## Platform support

| Platform | Wrapper | Status |
|---|---|---|
| Linux (x86_64, aarch64) | `scripts/linux/osat` | Supported |
| macOS (Intel, Apple Silicon) | `scripts/macos/osat` | Supported |
| Windows 11 (x86_64) | `scripts/windows-11/osat.cmd`, `osat.ps1` | Supported |

## License

MIT
