# Roadmap

## Near term

- Add `scripts/windows-10/` wrappers once Windows 10 is tested
- Add ARM64 Windows wrapper once tested
- Add a `--json` flag to osat.py for machine-readable output
- Add CI via GitHub Actions to verify installation on Linux, macOS, and Windows runners

## Pattern improvements

- Extract the common installer logic (version detection, wrapper rendering, gitignore management, PATH notes) into a shared `tool_installer.py` module that tool-specific installers can import
- Add a `--check` flag to the installer to verify an existing installation without reinstalling
- Document the pattern for tools that require a minimum Python version different from the system default
