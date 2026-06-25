# Restic Cross-Platform Filesystem Layout Specification

A platform-neutral convention for organizing restic binaries, configuration,
credentials, scripts, and logs consistently across Linux, macOS, and Windows.

---

## Standards Reference

### Linux — XDG Base Directory Specification

<https://specifications.freedesktop.org/basedir/latest/>

The authoritative standard for user-space file locations on Linux. Defines
environment variables with sensible defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `$XDG_CONFIG_HOME` | `~/.config` | User configuration files |
| `$XDG_DATA_HOME` | `~/.local/share` | User data files |
| `$XDG_STATE_HOME` | `~/.local/state` | Persistent state (logs, history) |
| `$XDG_CACHE_HOME` | `~/.cache` | Non-essential cached data |
| *(no variable)* | `~/.local/bin` | User executables |

### macOS — No Single Standard; Context Matters

macOS has two different conventions depending on the type of tool:

**GUI apps** (installed in `/Applications`) use `~/Library/`:
```
~/Library/Application Support/<AppName>/   ← config + data
~/Library/Caches/<AppName>/                ← cache
~/Library/Logs/<AppName>/                  ← logs
```

**CLI tools** — the ecosystem has converged on XDG paths, not `~/Library/`.
Tools like `git`, `bash`, `zsh`, `vim`, `gh`, `kubectl`, `terraform`, `docker`,
and even Apple's own CLI tools use `~/.config`. The `~/Library/` convention
does not apply to command-line tools and dotfile managers do not place config
there. Restic is a CLI tool — use XDG paths on macOS.

### Windows — Known Folders / AppData

Windows uses `%APPDATA%` and `%LOCALAPPDATA%` as the rough equivalents of
XDG directories:

| Windows | Equivalent XDG | Purpose |
|---------|----------------|---------|
| `%APPDATA%` (Roaming) | `$XDG_CONFIG_HOME` | Config — syncs in domain environments |
| `%LOCALAPPDATA%` (Local) | `$XDG_DATA_HOME` / `$XDG_STATE_HOME` | Data/state — machine-local |
| `%LOCALAPPDATA%` (Local) | `$XDG_CACHE_HOME` | Cache — machine-local |
| `%USERPROFILE%\bin` or `%LOCALAPPDATA%\Programs` | `~/.local/bin` | User executables |

> There is no formal Windows standard for CLI tools specifically. Many
> cross-platform CLI tools (scoop, gh, etc.) use XDG paths even on Windows
> when run under PowerShell or WSL.

---

## Our Layout vs. The Standards

### File-by-file comparison

| File | Our path | Linux XDG standard | macOS CLI convention | Windows convention | Compliant? |
|------|----------|--------------------|---------------------|--------------------|-----------|
| Binary | `~/bin/restic` | `~/.local/bin/restic` | `~/.local/bin/restic` | `%LOCALAPPDATA%\Programs\restic.exe` | ⚠️ Close — `~/bin` is valid but non-standard on Linux |
| Password | `~/.private/restic/password.txt` | No XDG equivalent for secrets | No standard | No standard | ✅ Good — intentionally non-standard for security |
| Env/config | `~/.config/restic/env` | `$XDG_CONFIG_HOME/restic/` = `~/.config/restic/` | `~/.config/restic/` | `%APPDATA%\restic\` | ✅ Correct on Linux + macOS; close on Windows |
| Excludes | `~/.config/restic/excludes.txt` | `$XDG_CONFIG_HOME/restic/` | `~/.config/restic/` | `%APPDATA%\restic\` | ✅ Correct on Linux + macOS |
| Script | `~/bin/restic-backup.sh` | `~/.local/bin/` | `~/.local/bin/` | `%LOCALAPPDATA%\Programs\` | ⚠️ Same as binary — `~/bin` is non-standard but common |
| Logs | `~/.local/share/restic/logs/` | `$XDG_STATE_HOME/restic/` = `~/.local/state/restic/` | `~/.local/state/restic/` | `%LOCALAPPDATA%\restic\logs\` | ⚠️ Should be `~/.local/state/` not `~/.local/share/` |

### Summary of gaps

**`~/bin/` vs `~/.local/bin/`**
Our spec uses `~/bin/` for the binary and script. The XDG spec says user
executables belong in `~/.local/bin/`. Both work — `~/bin/` is a longstanding
Unix convention and is widely used — but `~/.local/bin/` is the XDG-compliant
path and is what modern Linux distros add to PATH by default.

**`~/.local/share/` vs `~/.local/state/` for logs**
Logs are persistent state, not data. XDG added `$XDG_STATE_HOME`
(`~/.local/state/`) specifically for this: things like history, logs, and
application state that persist across restarts but aren't important enough to
live in `$XDG_DATA_HOME`. Our spec put logs in `~/.local/share/` which is
technically wrong — `~/.local/state/` is more correct.

**`~/.private/` for secrets**
Not part of any standard — intentionally. No OS standard defines a secure
credential location for user-space CLI tools. `~/.private/` is a reasonable
convention that signals "don't sync this" and is less likely to be touched
by dotfile managers or cloud sync tools.

---

## Recommended Revised Layout

Taking the above into account, the corrected OS-agnostic layout is:

```
~
├── .local/
│   ├── bin/
│   │   ├── restic                    ← binary (restic.exe on Windows)
│   │   └── restic-backup.sh          ← script (.ps1 on Windows)
│   └── state/
│       └── restic/
│           └── backup.log            ← persistent log (XDG_STATE_HOME)
│
├── .private/
│   └── restic/
│       └── password.txt              ← encryption password (non-standard, intentional)
│
└── .config/
    └── restic/
        ├── env                       ← environment variables
        ├── excludes.txt              ← global excludes
        ├── excludes-linux.txt        ← Linux-specific excludes
        ├── excludes-macos.txt        ← macOS-specific excludes
        └── excludes-windows.txt      ← Windows-specific excludes
```

### Platform path translation (revised)

| Concept | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Binary | `~/.local/bin/restic` | `~/.local/bin/restic` | `%LOCALAPPDATA%\Programs\restic.exe` |
| Script | `~/.local/bin/restic-backup.sh` | `~/.local/bin/restic-backup.sh` | `%LOCALAPPDATA%\Programs\restic-backup.ps1` |
| Password | `~/.private/restic/password.txt` | `~/.private/restic/password.txt` | `%USERPROFILE%\.private\restic\password.txt` |
| Env file | `~/.config/restic/env` | `~/.config/restic/env` | `%APPDATA%\restic\env.ps1` |
| Excludes | `~/.config/restic/excludes.txt` | `~/.config/restic/excludes.txt` | `%APPDATA%\restic\excludes.txt` |
| Logs | `~/.local/state/restic/backup.log` | `~/.local/state/restic/backup.log` | `%LOCALAPPDATA%\restic\logs\backup.log` |

### Scheduler config locations (unchanged)

| Platform | Scheduler | Config location |
|----------|-----------|----------------|
| Linux | systemd user timer | `~/.config/systemd/user/restic-backup.{service,timer}` |
| macOS | launchd | `~/Library/LaunchAgents/com.user.restic-backup.plist` |
| Windows | Task Scheduler | Configured via `schtasks` or GUI — no file convention |

---

## Permissions

| File | Linux/macOS | Windows |
|------|-------------|---------|
| `~/.local/bin/restic` | `755` | Default executable |
| `~/.local/bin/restic-backup.sh` | `755` | Default executable |
| `~/.private/restic/` | `700` | Owner only (ACL) |
| `~/.private/restic/password.txt` | `600` | Owner read only (ACL) |
| `~/.config/restic/env` | `600` | Owner read only (ACL) |
| `~/.config/restic/excludes*.txt` | `644` | Default |
| `~/.local/state/restic/` | `755` | Default |

---

## Notes

**Our existing setup on raw uses `~/bin/`** — this is fine in practice and
widely understood. Migrating to `~/.local/bin/` is optional but would make
the setup fully XDG-compliant. Most modern Ubuntu and Fedora installs
automatically add `~/.local/bin` to `$PATH` if it exists.

**macOS does not set XDG variables by default** — scripts should always
fall back to the default paths explicitly rather than relying on the variables
being set:
```sh
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
```

**Windows and `~/bin/`** — Windows does not have a `~/bin/` convention.
Use `%LOCALAPPDATA%\Programs\` for user-installed executables without
admin rights.

**Cloud sync** — ensure `~/.private/` is excluded from Dropbox, iCloud,
OneDrive, and Syncthing. Do not assume dotfiles are excluded automatically.

