# Restic Server-Side Filesystem Layout Specification

A convention for deploying restic as a system-level backup service on Linux
servers, following the Filesystem Hierarchy Standard (FHS) and systemd
conventions. This is the companion to `restic-platform-paths-spec.md` which
covers desktop/user-level deployments.

---

## Standards Reference

### Filesystem Hierarchy Standard (FHS)

<https://refspecs.linuxfoundation.org/fhs.shtml>

The authoritative standard for file locations on Linux systems. Key directories:

| Path | Purpose |
|------|---------|
| `/etc/` | System-wide configuration files |
| `/usr/local/bin/` | Locally installed user-facing executables |
| `/usr/local/sbin/` | Locally installed system/admin executables |
| `/var/lib/` | Persistent application state and data |
| `/var/log/` | Log files |
| `/var/run/` or `/run/` | Runtime data (PIDs, sockets) — not persistent across reboots |
| `/tmp/` | Temporary files — cleared on reboot |

### systemd Service Conventions

System-level services (run as dedicated accounts, not login users) use:

```
/etc/systemd/system/restic-backup.service
/etc/systemd/system/restic-backup.timer
```

Enabled and managed via `systemctl` (without `--user`).

---

## Key Differences from Desktop Deployment

| Aspect | Desktop (XDG) | Server (FHS) |
|--------|--------------|--------------|
| Runs as | Login user (`initial`) | Dedicated service account (`restic` or `backup`) |
| Config | `~/.config/restic/` | `/etc/restic/` |
| Data | `~/.local/share/restic/` | `/var/lib/restic/` |
| Logs | `~/.local/state/restic/` | `/var/log/restic/` |
| Binary | `~/.local/bin/restic` | `/usr/local/bin/restic` |
| Scripts | `~/.local/bin/` | `/usr/local/sbin/` |
| Secrets | `~/.private/restic/` | `/etc/restic/` (strict ACL) or secrets manager |
| Automation | systemd user timer | systemd system service |
| Elevation | None needed | Script runs as service account |

---

## Directory Layout

```
/
├── etc/
│   └── restic/
│       ├── password.txt              ← restic repo encryption password
│       ├── env                       ← environment variable definitions
│       ├── excludes.txt              ← global excludes
│       └── excludes-<hostname>.txt   ← host-specific excludes (optional)
│
├── usr/
│   └── local/
│       ├── bin/
│       │   └── restic                ← restic binary
│       └── sbin/
│           └── restic-backup.sh      ← backup script (root/service account only)
│
├── var/
│   ├── lib/
│   │   └── restic/                   ← local restic state (cache, locks)
│   └── log/
│       └── restic/
│           └── backup.log            ← backup run log
│
└── etc/
    └── systemd/
        └── system/
            ├── restic-backup.service ← systemd service unit
            └── restic-backup.timer   ← systemd timer unit
```

---

## Service Account Setup

Create a dedicated unprivileged user for running backups:

```bash
sudo useradd \
  --system \
  --no-create-home \
  --shell /usr/sbin/nologin \
  --comment "Restic backup service" \
  restic
```

> Using a dedicated account limits blast radius if the backup script or
> credentials are ever compromised. The account has no login shell and
> no home directory.

---

## File Descriptions

### `/etc/restic/password.txt`
The restic repository encryption password. Owned by root, readable only
by the service account:

```bash
sudo touch /etc/restic/password.txt
sudo chown root:restic /etc/restic/password.txt
sudo chmod 640 /etc/restic/password.txt
# Then write the password:
sudo nano /etc/restic/password.txt
```

### `/etc/restic/env`
Environment variable definitions sourced by the backup script:

```bash
export RESTIC_REPOSITORY="sftp:initial@192.168.1.100:/mnt/backup/restic/$(hostname)"
export RESTIC_PASSWORD_FILE="/etc/restic/password.txt"
```

Permissions:
```bash
sudo chown root:restic /etc/restic/env
sudo chmod 640 /etc/restic/env
```

### `/etc/restic/excludes.txt`
Exclude patterns. On a server this typically includes:

```
/proc/*
/sys/*
/dev/*
/run/*
/tmp/*
/var/tmp/*
/var/cache/*
/var/lib/restic/*
/lost+found
*.sock
*.pid
/var/log/restic/*
```

### `/usr/local/bin/restic`
The restic binary. Installed system-wide:

```bash
sudo install -o root -g root -m 755 /path/to/restic /usr/local/bin/restic
```

Or via package manager:
```bash
sudo apt install restic
```

### `/usr/local/sbin/restic-backup.sh`
The backup script. Owned by root, executable by the service account:

```bash
#!/usr/bin/env bash
set -e -o pipefail

source /etc/restic/env

# Unlock stale locks
/usr/local/bin/restic unlock

# Run the backup
/usr/local/bin/restic backup \
  --one-file-system \
  --exclude-file /etc/restic/excludes.txt \
  /home \
  /etc \
  /var/lib \
  /srv

# Retention policy
/usr/local/bin/restic forget \
  --keep-daily 14 \
  --keep-weekly 8 \
  --keep-monthly 6 \
  --prune

# Verify integrity
/usr/local/bin/restic check

echo "Backup completed at $(date)" >> /var/log/restic/backup.log
```

```bash
sudo install -o root -g restic -m 750 restic-backup.sh /usr/local/sbin/restic-backup.sh
```

### `/var/lib/restic/`
Local restic cache and state. Owned by the service account:

```bash
sudo mkdir -p /var/lib/restic
sudo chown restic:restic /var/lib/restic
sudo chmod 750 /var/lib/restic
```

Set in env file:
```bash
export RESTIC_CACHE_DIR="/var/lib/restic/cache"
```

### `/var/log/restic/`
Log directory. Writable by the service account:

```bash
sudo mkdir -p /var/log/restic
sudo chown restic:restic /var/log/restic
sudo chmod 750 /var/log/restic
```

---

## systemd Service and Timer

### `/etc/systemd/system/restic-backup.service`

```ini
[Unit]
Description=Restic backup
After=network-online.target
Wants=network-online.target
ConditionPathIsMountPoint=/mnt/backup

[Service]
Type=oneshot
User=restic
Group=restic
ExecStart=/usr/local/sbin/restic-backup.sh
StandardOutput=append:/var/log/restic/backup.log
StandardError=append:/var/log/restic/backup.log

# Security hardening
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/restic /var/log/restic
```

### `/etc/systemd/system/restic-backup.timer`

```ini
[Unit]
Description=Run restic backup daily

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
```

> `RandomizedDelaySec=1800` spreads backup start time up to 30 minutes
> randomly — useful when multiple servers back up to the same target.

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now restic-backup.timer
sudo systemctl list-timers restic-backup.timer
```

Check logs:
```bash
sudo journalctl -u restic-backup.service --since today
sudo tail -f /var/log/restic/backup.log
```

---

## Log Rotation

Add `/etc/logrotate.d/restic`:

```
/var/log/restic/backup.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
    create 640 restic restic
}
```

---

## Permissions Summary

| Path | Owner | Group | Mode | Notes |
|------|-------|-------|------|-------|
| `/etc/restic/` | root | restic | `750` | Directory |
| `/etc/restic/password.txt` | root | restic | `640` | Group readable |
| `/etc/restic/env` | root | restic | `640` | Group readable |
| `/etc/restic/excludes.txt` | root | restic | `644` | World readable fine |
| `/usr/local/bin/restic` | root | root | `755` | System binary |
| `/usr/local/sbin/restic-backup.sh` | root | restic | `750` | Group executable |
| `/var/lib/restic/` | restic | restic | `750` | Service account owns |
| `/var/log/restic/` | restic | restic | `750` | Service account owns |

---

## What Gets Backed Up on a Server

Unlike a desktop where you back up the home directory, on a server the
important paths are typically:

```
/etc/          ← all system configuration
/home/         ← user home directories (if applicable)
/var/lib/      ← application data (databases, app state)
/srv/          ← served data (web roots, file shares)
/root/         ← root home directory (optional)
/usr/local/    ← locally installed software and scripts
```

Explicitly exclude:
```
/proc/ /sys/ /dev/ /run/    ← virtual filesystems
/tmp/ /var/tmp/             ← temporary data
/var/cache/                 ← regeneratable cache
/var/log/restic/            ← don't back up backup logs
/lost+found                 ← filesystem artifacts
```

---

## Note on Our Current Setup

**flow** currently runs restic as the `initial` login user rather than a
dedicated service account. This works fine but is not FHS-compliant. To
harden flow toward a proper server deployment, the migration path would be:

1. Create a `restic` system account
2. Move config to `/etc/restic/`
3. Move the binary to `/usr/local/bin/restic`
4. Move the script to `/usr/local/sbin/restic-backup.sh`
5. Move cache/state to `/var/lib/restic/`
6. Move logs to `/var/log/restic/`
7. Convert the systemd user timer to a system-level service
8. Grant the `restic` account read access to `/mnt/backup/`

