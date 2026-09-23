---
name: clean-my-mac
description: >
  Clean up development caches and build artifacts on macOS to free disk space.
  Use this skill when the user wants to clean their Mac, free up disk space,
  remove development caches, or mentions things like "clean my mac", "free up space",
  "disk full", "磁盘满了", "清理缓存", "释放空间", or asks about what's taking up space
  from development tools like Gradle, Docker, npm, Maven, Homebrew, Xcode, etc.
  This skill analyzes disk usage, presents a clear report, and only deletes after
  user confirmation.
---

# Clean My Mac

A safe, interactive skill for cleaning macOS development caches and build artifacts.

## Core Principles

1. **Safety first**: Always analyze and present findings before deleting anything
2. **Transparency**: Show the user exactly what will be cleaned and how much space it will free
3. **Confirmation required**: Never delete without explicit user approval
4. **Selective cleanup**: Let users choose what to keep or remove

## Workflow

### Step 1: Analyze Disk Usage

Run the analysis script to scan common development cache directories:

```bash
python3 <skill-dir>/scripts/analyze.py
```

This produces a JSON report of all found directories with their sizes.

### Step 2: Present Analysis to User

Format the analysis results into a clear, readable table:

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔍 Disk Usage Analysis                       │
├─────────────────────┬───────────────┬───────────────────────────┤
│ Category            │ Size          │ Path                      │
├─────────────────────┼───────────────┼───────────────────────────┤
│ Gradle Caches       │ 9.5 GB        │ ~/.gradle/caches          │
│ Gradle Wrapper      │ 3.8 GB        │ ~/.gradle/wrapper/dists   │
│ Docker Volumes      │ 22.5 GB       │ (111 dangling volumes)    │
│ npm Cache           │ 1.2 GB        │ ~/.npm/_cacache           │
│ Homebrew Cache      │ 0.8 GB        │ ~/Library/Caches/Homebrew │
│ Xcode DerivedData   │ 15.3 GB       │ ~/Library/Developer/...   │
├─────────────────────┼───────────────┼───────────────────────────┤
│ TOTAL               │ 53.1 GB       │                           │
└─────────────────────┴───────────────┴───────────────────────────┘
```

Ask the user which categories they want to clean. For some categories, offer options:
- **Gradle**: Clean all versions? Or keep latest N versions?
- **Docker**: Remove all dangling? Or unused images too?
- **Xcode**: Remove all? Or only old projects?

**Classify every item before presenting it.** Disk usage is not the same as
disk waste. Label each row so the user can decide:

| Label | Meaning | Example |
|-------|---------|---------|
| 🟢 cache | Regenerated on demand, zero information loss | `Service Worker/CacheStorage`, `Cache`, `CachedExtensionVSIXs` |
| 🟡 state | Convenience data; losing it costs you layout/undo/history | `User/workspaceStorage`, `User/History`, `User/globalStorage` |
| 🔴 data | Real user content — never propose without an explicit request | databases, documents, project sources |

Report both the **grand total** of the directory and the **safe-to-reclaim
subtotal**, and say plainly which is which. "30 GB used, 27 GB is safe cache" is
a far more useful answer than a raw size list.

When a stale-state category is offered, quantify the dead portion rather than the
whole thing — e.g. "1.5 GB of 2.9 GB workspace state points at deleted projects"
lets the user reclaim most of it while keeping live project state.

### Step 3: Execute Cleanup (After Confirmation)

Once the user confirms, run the cleanup script. Categories are **space-separated**:

```bash
python3 <skill-dir>/scripts/clean.py --categories gradle-caches gradle-wrapper docker-volumes npm-cache vscode-webview-cache vscode-http-cache
```

Verify the target is idle before deleting — for VS Code-family caches the editor
must be closed. The scripts enforce this themselves, but the report will show the
category as skipped rather than cleaned if the app is open, so check up front.

### Step 4: Report Results

Show before/after comparison:

```
✅ Cleanup Complete!

┌─────────────────────────────────────┬───────────────┬───────────────┐
│ Category                            │ Before        │ After         │
├─────────────────────────────────────┼───────────────┼───────────────┤
│ Gradle Caches                       │ 9.5 GB        │ 0 B           │
│ Gradle Wrapper                      │ 3.8 GB        │ 1.3 GB        │
│ Docker Volumes                      │ 22.5 GB       │ 3.4 GB        │
├─────────────────────────────────────┼───────────────┼───────────────┤
│ TOTAL RECLAIMED                     │               │ 32.1 GB       │
└─────────────────────────────────────┴───────────────┴───────────────┘
```

## Supported Categories

### System caches

| Category ID | Description | Default Behavior |
|-------------|-------------|------------------|
| `gradle-caches` | ~/.gradle/caches | Remove all (safe) |
| `gradle-wrapper` | ~/.gradle/wrapper/dists | Keep latest N versions |
| `docker-images` | Docker dangling images | Remove dangling only |
| `docker-volumes` | Docker dangling volumes | Remove dangling only |
| `docker-containers` | Docker stopped containers | Remove stopped only |
| `npm-cache` | ~/.npm/_cacache | Remove all (safe) |
| `yarn-cache` | ~/.cache/yarn | Remove all (safe) |
| `pnpm-store` | ~/Library/pnpm/store | Remove unused |
| `maven-cache` | ~/.m2/repository | Remove all (safe) |
| `homebrew-cache` | ~/Library/Caches/Homebrew | Remove all (safe) |
| `xcode-deriveddata` | ~/Library/Developer/Xcode/DerivedData | Remove all |
| `xcode-archives` | ~/Library/Developer/Xcode/Archives | Remove all |

### VS Code family (Code / Insiders / Cursor / VSCodium / Windsurf)

These editors share the same Electron user-data layout and are detected by the
presence of their `~/Library/Application Support/<app>` directory, so anything
installed is handled automatically.

| Category ID | Path (relative to the app's user-data dir) | Default Behavior |
|-------------|--------------------------------------------|------------------|
| `vscode-webview-cache` | `Service Worker/CacheStorage` | Remove all — **usually the biggest win** |
| `vscode-webstorage` | `WebStorage` | Remove all (safe) |
| `vscode-http-cache` | `Cache` | Remove all (safe) |
| `vscode-vsix-cache` | `CachedExtensionVSIXs` | Remove all (safe) |
| `vscode-stale-workspaces` | `User/workspaceStorage` | Only entries whose project folder is gone |
| `vscode-history-orphaned` | `User/History` | **Opt-in only** — only entries whose file is gone |

**`vscode-webview-cache` is normally the single largest reclaimable item and it
never self-expires.** It is an ephemeral webview resource cache (one directory
can hold 100k+ files), so it can silently grow to tens of GB. Deleting it is
always safe — VS Code re-fetches on demand.

#### Safety rules for editor categories

1. **The editor must be closed.** Electron holds these files open; cleaning a
   running instance is a no-op at best and corrupts state at worst. The scripts
   check with `pgrep` and skip any running app, reporting it instead.
2. **Opt-in categories are never included in `all`.**
   `vscode-history-orphaned` is a data store (undo-over-time), not a cache, so
   it must be requested explicitly by name.
3. **`/Volumes/*` paths are always kept.** A missing project under an external
   drive usually just means the drive is unmounted, not that it was deleted.

## Options

```bash
# See what would be cleaned without touching anything
python3 <skill-dir>/scripts/clean.py --dry-run --categories vscode-http-cache

# Gradle wrapper: keep the 3 most recent versions
python3 <skill-dir>/scripts/clean.py --categories gradle-wrapper --keep-latest 3
```

`all` expands to every category **except** the opt-in ones.

## Edge Cases

- **Permission denied**: Some directories may require elevated permissions. Skip and report.
- **Directory not found**: Simply skip and note it wasn't present.
- **Active containers**: Never remove running Docker containers. Only remove stopped ones.
- **Git repositories**: Never delete anything inside .git directories.
- **Editor running**: Never clean VS Code-family caches while the app is open; the scripts skip it and say so.
- **Unmounted external drives**: Never prune workspace/history entries under `/Volumes/*`; the path is only "missing" because the drive is detached.
- **Custom cache locations**: If user mentions a specific path, add it to analysis.
- **User points at a specific directory**: If the request names one directory (e.g.
  `~/Library/Application Support/Code`), recurse with `du -sh */ | sort -hr` first,
  identify what each subdirectory actually is, and classify it as
  cache / state / data before proposing anything. Report both the grand total and
  the safe-to-reclaim subtotal.

## Scripts

The `scripts/` directory contains:
- `analyze.py` — Scans system and produces JSON report
- `clean.py` — Executes cleanup based on selected categories

Run with `--help` for usage information.
