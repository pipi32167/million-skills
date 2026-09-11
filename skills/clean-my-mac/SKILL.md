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

### Step 3: Execute Cleanup (After Confirmation)

Once the user confirms, run the cleanup script:

```bash
python3 <skill-dir>/scripts/clean.py --categories gradle-caches,gradle-wrapper,docker-volumes,npm-cache
```

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

## Edge Cases

- **Permission denied**: Some directories may require elevated permissions. Skip and report.
- **Directory not found**: Simply skip and note it wasn't present.
- **Active containers**: Never remove running Docker containers. Only remove stopped ones.
- **Git repositories**: Never delete anything inside .git directories.
- **Custom cache locations**: If user mentions a specific path, add it to analysis.

## Scripts

The `scripts/` directory contains:
- `analyze.py` — Scans system and produces JSON report
- `clean.py` — Executes cleanup based on selected categories

Run with `--help` for usage information.
