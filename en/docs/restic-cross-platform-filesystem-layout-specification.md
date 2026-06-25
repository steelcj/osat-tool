# Restic Cross-Platform Filesystem Layout Specification

A platform-neutral convention for organizing restic binaries, configuration,
credentials, scripts, and logs consistently across Windows, macOS, and Linux.

---

## Design Principles

- All paths resolve relative to the user home directory (`~`) — no root/admin paths
- No platform-specific environment variables in config files (no `%APPDATA%`, no `/home/`)
- Secrets isolated in `~/.private/` — a non-standard directory less likely to be synced by cloud tools
- Config isolated in `~/.config/restic/` — XDG-compliant on Linux, valid on macOS and Windows
- Binary and scripts isolated in `~/bin/` — one location to add to PATH on all platforms
- Logs isolated in `~/.local/share/restic/logs/` — keeps home clean, writable without elevation

---

## Directory Layout

```
~
├── bin/
│   ├── restic                        ← restic binary (restic.exe on Windows)
│   └── restic-backup.sh              ← backup script (.ps1 on Windows)
│
├── .private/
│   └── restic/
│       └── password.txt              ← restic repo encryption password
│
├── .config/
│   └── restic/
│       ├── env                       ← environment variable definitions
│       ├── excludes.txt              ← global excludes (all platforms)
│       ├── excludes-linux.txt        ← Linux-specific excludes
│       ├── excludes-macos.txt        ← macOS-specific excludes
│       └── excludes-windows.txt      ← Windows-specific excludes
│
└── .local/
    └── share/
        └── restic/
            └── logs/
                └── backup.log        ← backup run log
```

---

## File Descriptions

### `~/bin/restic`
The restic binary. Installed here to avoid requiring elevated privileges.
On Windows: `~/bin/restic.exe`

### `~/bin/restic-backup.sh`
The backup script. Sources `~/.config/restic/env` at runtime.
On Windows: `~/bin/restic-backup.ps1`

### `~/.private/restic/password.txt`
The restic repository encryption password. Must be protected:

| Platform | Permissions |
|----------|-------------|
| Linux / macOS | `chmod 600` — owner read/write only |
| Windows | Remove inherited permissions, grant owner read only via ACL |

> `~/.private/` is intentionally non-standard. Dropbox, iCloud, OneDrive, and
> similar tools do not sync dotfiles beginning with `.` by default on most platforms,
> reducing the risk of accidental credential exposure.

### `~/.config/restic/env`
Defines RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE, and any other restic
environment variables. Sourced by the backup script at runtime rather than
loaded from the shell profile, so it works in non-interactive contexts
(systemd, launchd, Task Scheduler).

Example contents:
```sh
export RESTIC_REPOSITORY="sftp:user@192.168.1.100:/mnt/backup/restic/hostname"
export RESTIC_PASSWORD_FILE="$HOME/.private/restic/password.txt"
```

On Windows (PowerShell):
```powershell
$env:RESTIC_REPOSITORY = "sftp:user@192.168.1.100:/mnt/backup/restic/hostname"
$env:RESTIC_PASSWORD_FILE = "$HOME\.private\restic\password.txt"
```

### `~/.config/restic/excludes.txt`
Global excludes that apply on all platforms:
```
*.log
*.tmp
node_modules
**/.git/*
**/build/*
**/dist/*
```

### `~/.config/restic/excludes-linux.txt`
Linux-specific excludes:
```
.cache/*
.local/share/Trash/*
.thumbnails/*
/home/USER/snap/*
/home/USER/iso/*
/home/USER/Downloads/*
/proc/*
/sys/*
/dev/*
/run/*
```

### `~/.config/restic/excludes-macos.txt`
macOS-specific excludes:
```
Library/Caches/*
Library/Logs/*
Library/Application Support/*/Cache/*
.Trash/*
/Users/USER/Downloads/*
/private/tmp/*
/private/var/*
*.DS_Store
```

### `~/.config/restic/excludes-windows.txt`
Windows-specific excludes:
```
AppData/Local/Temp/*
AppData/Local/Microsoft/Windows/INetCache/*
AppData/Local/*/Cache/*
$Recycle.Bin/*
pagefile.sys
hiberfil.sys
swapfile.sys
```

### `~/.local/share/restic/logs/backup.log`
Append-only log of backup runs. The backup script appends a timestamped
summary after each run. On Windows, use `~/AppData/Local/restic/logs/backup.log`
as `~/.local/` is not conventional there.

---

## Platform Path Translation

| Concept | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Home | `/home/user` | `/Users/user` | `C:\Users\user` |
| Binary | `~/bin/restic` | `~/bin/restic` | `~\bin\restic.exe` |
| Script | `~/bin/restic-backup.sh` | `~/bin/restic-backup.sh` | `~\bin\restic-backup.ps1` |
| Password | `~/.private/restic/password.txt` | `~/.private/restic/password.txt` | `~\.private\restic\password.txt` |
| Env file | `~/.config/restic/env` | `~/.config/restic/env` | `~\.config\restic\env.ps1` |
| Excludes | `~/.config/restic/excludes.txt` | `~/.config/restic/excludes.txt` | `~\.config\restic\excludes.txt` |
| Logs | `~/.local/share/restic/logs/` | `~/.local/share/restic/logs/` | `~\AppData\Local\restic\logs\` |

---

## Scheduler Config Locations

| Platform | Scheduler | Config location |
|----------|-----------|----------------|
| Linux | systemd user timer | `~/.config/systemd/user/restic-backup.service` |
| Linux | systemd user timer | `~/.config/systemd/user/restic-backup.timer` |
| macOS | launchd | `~/Library/LaunchAgents/com.user.restic-backup.plist` |
| Windows | Task Scheduler | Configured via GUI or `schtasks` — no file convention |

---

## Permissions Summary

| File | Linux/macOS | Windows |
|------|-------------|---------|
| `~/bin/restic` | `755` | Default executable |
| `~/bin/restic-backup.sh` | `755` | Default executable |
| `~/.private/restic/` | `700` | Owner only |
| `~/.private/restic/password.txt` | `600` | Owner read only (ACL) |
| `~/.config/restic/env` | `600` | Owner read only (ACL) |
| `~/.config/restic/excludes*.txt` | `644` | Default |
| `~/.local/share/restic/logs/` | `755` | Default |

---

## Notes

**Cloud sync tools** (Dropbox, iCloud, OneDrive, Syncthing): ensure `~/.private/`
is excluded from sync. Verify your sync tool's ignore rules explicitly — do not
assume dotfiles are excluded.

**Windows path separators**: restic on Windows accepts both `\` and `/` in paths.
Use `/` in restic repository paths for consistency with SFTP targets.

**Keyfiles**: if using a LUKS keyfile or SSH key for unattended operation, store
it under `~/.private/restic/` with `chmod 400` (Linux/macOS) or equivalent ACL (Windows).

**Multiple machines**: use a per-machine subdirectory in the repository path:
```
sftp:user@host:/mnt/backup/restic/<hostname>/
```
This keeps snapshots from different machines isolated within one repository root.

