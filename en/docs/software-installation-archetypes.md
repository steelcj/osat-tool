# Software Installation Archetypes

A platform-neutral taxonomy of how software gets installed, where it lives,
and the tradeoffs of each approach. Covers Linux, macOS, and Windows.

---

## The Core Dimensions

Every installation decision involves four axes:

| Dimension | Question |
|-----------|----------|
| **Runtime dependency** | Is the tool self-contained, or does it need a language runtime? |
| **Isolation** | Does the install affect other tools, users, or the system? |
| **Privilege** | Does installing or running it require elevation? |
| **Scope** | Who can use it — one user, all users, or a service account? |

These dimensions produce six distinct archetypes.

---

## The Six Archetypes

### 1. System Package

Installed by the OS package manager into system-wide paths. Available to all
users and services. Managed by the distribution or OS vendor.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Tool** | apt, dnf, pacman | — (no built-in) | winget (GUI/system apps) |
| **Binary** | `/usr/bin/` | N/A | `C:\Program Files\` |
| **Config** | `/etc/<tool>/` | N/A | Registry / `%ProgramData%` |
| **Privilege** | root required | N/A | Admin / UAC required |
| **Examples** | `apt install restic` | — | `winget install Git.Git` |

### Advantages

* Managed updates, dependency resolution, and easy removal
* Available to all users and services on the machine
* Distro-tested for compatibility

### Disadvantages

* Requires root or admin to install
* Often lags behind upstream releases
* No per-user version control — everyone gets the same version

**macOS note:** macOS ships no general-purpose system package manager.
The App Store covers GUI apps; CLI tools have no native equivalent at this level.

---

### 2. System Local

Installed by an admin into `/usr/local/` (Linux/macOS) or a shared programs
directory (Windows). Used for software not available via the package manager,
or to pin a specific version.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Binary** | `/usr/local/bin/` | `/usr/local/bin/` | `C:\Tools\` or `C:\ProgramData\` |
| **Config** | `/etc/<tool>/` | `/etc/<tool>/` | `%ProgramData%\<tool>\` |
| **Privilege** | root required | sudo required | Admin required |
| **Examples** | Custom restic binary | Manually installed Go binary | Manually extracted .exe |

### Advantages

* Available system-wide without package manager overhead
* Full version control — install exactly what you want
* No dependency on a package repository

### Disadvantages

* Manual update management — no automatic upgrades
* Still requires elevation to install
* No dependency resolution

---

### 3. Service Deployment

Software installed to run as a background daemon. Runs as a dedicated
unprivileged service account, not a login user. Follows the Filesystem
Hierarchy Standard (FHS) on Linux.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Binary** | `/usr/local/bin/` | `/usr/local/bin/` | `%ProgramFiles%\` |
| **Config** | `/etc/<tool>/` | `/etc/<tool>/` or launchd plist | `%ProgramData%\<tool>\` |
| **Data** | `/var/lib/<tool>/` | `/var/lib/<tool>/` | `%ProgramData%\<tool>\` |
| **Logs** | `/var/log/<tool>/` | `/var/log/<tool>/` | `%ProgramData%\<tool>\logs\` |
| **Scheduler** | systemd system service | launchd (system domain) | Windows Service / Task Scheduler |
| **Runs as** | Dedicated service account | Dedicated service account | SYSTEM or service account |
| **Privilege** | root to install and configure | root to install and configure | Admin to install |
| **Examples** | nginx, restic daemon, sshd | nginx, restic daemon | IIS, SQL Server |

### Advantages

* Least-privilege runtime — service account has minimal permissions
* Runs independently of any user login session
* Proper log rotation and systemd supervision
* Clean separation between config, data, and logs

### Disadvantages

* More complex to set up than user-level installs
* Requires root or admin to install and configure
* Service account management adds operational overhead

**Note:** This is not a system-wide install. The binary may be system-wide but
the config, credentials, data, and automation are scoped to the service account.

---

### 4. Package Manager (User-Scoped)

A user-level package manager that installs into the user's home directory
without requiring elevation. The modern sweet spot for developer tooling.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Tool** | Homebrew (Linux), Nix | Homebrew | Scoop, winget `--scope user` |
| **Binary** | `~/.linuxbrew/bin/` | `/opt/homebrew/bin/` (Apple Silicon) `/usr/local/bin/` (Intel) | `%USERPROFILE%\scoop\shims\` |
| **Config** | `~/.config/` | `~/.config/` | `%APPDATA%\` |
| **Privilege** | None | None | None |
| **Updates** | `brew upgrade` | `brew upgrade` | `scoop update *` |
| **Examples** | `brew install restic` | `brew install restic` | `scoop install restic` |

### Advantages

* No root or admin required
* Managed updates via a single command
* Reproducible — export and import package lists across machines
* Large curated package catalogs

### Disadvantages

* Not available to other users or system services
* Homebrew on macOS installs to `/opt/homebrew/` which is outside `~` — shared but non-system
* Adds a dependency on the package manager itself

**macOS note:** Homebrew is the de facto standard for CLI tools on macOS.
Even though it installs to `/opt/homebrew/`, it does not require sudo for
`brew install` commands. It is the closest macOS equivalent to `apt`.

**Windows note:** Scoop installs CLI tools without admin rights, into the
user profile, and does not pollute the system PATH — instead using shims in a
single directory. winget with `--scope user` achieves similar results for
supported packages.

---

### 5. User XDG / Manual User Install

The tool is installed directly by and for a single user, living entirely under
`~`. No package manager involved. Best for self-contained binaries with no
runtime dependencies.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Binary** | `~/.local/bin/` (XDG) or `~/bin/` | `~/.local/bin/` or `~/bin/` | `%USERPROFILE%\bin\` or `%LOCALAPPDATA%\Programs\` |
| **Config** | `~/.config/<tool>/` | `~/.config/<tool>/` | `%APPDATA%\<tool>\` |
| **Data** | `~/.local/share/<tool>/` | `~/.local/share/<tool>/` | `%LOCALAPPDATA%\<tool>\` |
| **State/logs** | `~/.local/state/<tool>/` | `~/.local/state/<tool>/` | `%LOCALAPPDATA%\<tool>\logs\` |
| **Secrets** | `~/.private/<tool>/` | `~/.private/<tool>/` | `%USERPROFILE%\.private\<tool>\` |
| **Scheduler** | systemd user timer | launchd user agent | Task Scheduler (user context) |
| **Privilege** | None | None | None |
| **Examples** | restic on raw, restic on macOS | restic on macOS | restic on Windows |

### Advantages

* No root or admin required
* Full control over the exact version installed
* Completely isolated from the system and other users
* Best fit for self-contained binaries — Go and Rust tools like restic

### Disadvantages

* Manual update management — no automatic upgrades
* Not available to other users or service accounts
* PATH must be configured manually if `~/.local/bin/` is not already included

**This is our current setup on raw.** Restic is a self-contained Go binary
with no runtime dependencies — User XDG is the correct archetype.

---

### 6. Isolated User (Runtime-Dependent)

Used when the tool has a language runtime dependency (Python, Node, Ruby).
The tool and its entire dependency tree are sandboxed into an isolated
environment, preventing conflicts with other tools or the system runtime.

| | Linux | macOS | Windows |
|-|-------|-------|---------|
| **Tool** | pipx, nvm, rbenv, pyenv | pipx, nvm, rbenv | pipx, nvm, scoop |
| **Binary** | `~/.local/bin/<tool>` (shim) | `~/.local/bin/<tool>` (shim) | `%USERPROFILE%\.local\bin\` |
| **Environment** | `~/.local/share/pipx/venvs/<tool>/` | `~/.local/share/pipx/venvs/<tool>/` | `%USERPROFILE%\.local\share\pipx\venvs\` |
| **Config** | `~/.config/` | `~/.config/` | `%APPDATA%\` |
| **Privilege** | None | None | None |
| **Examples** | `pipx install ansible` | `pipx install ansible` | `pipx install ansible` |

### Advantages

* No root or admin required
* Complete isolation — no Python or Node version conflicts between tools
* Each tool gets its own pinned dependency versions
* Shim in PATH means the tool feels like a native binary to the user

### Disadvantages

* More disk space than a plain binary install
* Runtime must still be present on the system (pipx needs Python, nvm needs Node)
* Adds a layer of complexity — another tool to understand and maintain
* Not appropriate for self-contained binaries — unnecessary overhead

**This is the correct archetype for Ansible**, which is Python-dependent.
Not appropriate for restic, which has no runtime dependency.

---

## Decision Tree

```
Does the tool run as a background service?
  └─ Yes → Service Deployment (archetype 3)
  └─ No ↓

Does it need to be available to all users on the machine?
  └─ Yes + have admin rights → System Package or System Local (1 or 2)
  └─ No ↓

Does the tool have a language runtime dependency (Python, Node, Ruby)?
  └─ Yes → Isolated User / pipx / nvm (archetype 6)
  └─ No ↓

Is it a self-contained binary?
  └─ Yes → User XDG / Manual User Install (archetype 5)
  └─ No ↓

Do you want managed updates and a package catalog?
  └─ Yes → Package Manager User-Scoped / Homebrew / Scoop (archetype 4)
  └─ No  → User XDG / Manual User Install (archetype 5)
```

---

## Package Manager Comparison by Platform

| Manager | Platform | Scope | Admin needed | Best for |
|---------|----------|-------|-------------|---------|
| apt / dnf / pacman | Linux | System | Yes | System packages |
| Homebrew | macOS + Linux | User | No | CLI tools, dev tooling |
| winget | Windows | System or user | System: yes, User: no | GUI apps, Microsoft catalog |
| Scoop | Windows | User | No | CLI/portable tools |
| Chocolatey | Windows | System | Yes | Broader app catalog |
| pipx | Linux/macOS/Windows | User (isolated) | No | Python CLI tools |
| nvm / fnm | Linux/macOS/Windows | User (isolated) | No | Node.js tools |
| rbenv / rvm | Linux/macOS | User (isolated) | No | Ruby tools |
| Nix | Linux/macOS | Either | Configurable | Reproducible/declarative |

---

## Applied to Our Stack

| Tool | Archetype | Rationale |
|------|-----------|-----------|
| restic on raw | User XDG (5) | Self-contained Go binary, no runtime deps, single user |
| restic on flow | User XDG (5) | Same — flow is user-operated, not a hardened server |
| restic on a hardened server | Service Deployment (3) | Needs dedicated account, system-level scheduling |
| ansible | Isolated User (6) | Python-dependent, pipx is the correct install method |
| apt-installed restic | System Package (1) | Available to all users, managed by distro |
| brew-installed restic | Package Manager (4) | User-scoped, managed updates, no admin |
| scoop-installed restic | Package Manager (4) | Windows equivalent of brew for CLI tools |

---

## Key Insight

The archetype is determined by the tool's nature, not personal preference.

* Self-contained binary → User XDG or Package Manager (user-scoped)
* Runtime-dependent CLI → Isolated User (pipx, nvm, rbenv)
* Background daemon → Service Deployment
* System-wide utility → System Package or System Local

Mixing archetypes for the same tool on the same machine (for example both
`apt install restic` and `~/.local/bin/restic`) causes confusion about
which version runs and who manages updates. Pick one and be consistent.

