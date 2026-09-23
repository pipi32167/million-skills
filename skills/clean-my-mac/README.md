# clean-my-mac

🧹 Clean up macOS development caches and build artifacts to free disk space.

## What it cleans

| Category | Description |
|----------|-------------|
| Gradle Caches | ~/.gradle/caches |
| Gradle Wrapper | ~/.gradle/wrapper/dists (keeps latest version) |
| Docker Volumes | Dangling volumes |
| Docker Images | Unused images |
| npm Cache | ~/.npm/_cacache |
| Yarn Cache | ~/.cache/yarn |
| pnpm Store | ~/Library/pnpm/store |
| Maven Repository | ~/.m2/repository |
| Homebrew Cache | ~/Library/Caches/Homebrew |
| Xcode DerivedData | ~/Library/Developer/Xcode/DerivedData |
| Xcode Archives | ~/Library/Developer/Xcode/Archives |
| VS Code Webview Cache | `<userData>/Service Worker/CacheStorage` |
| VS Code WebStorage | `<userData>/WebStorage` |
| VS Code HTTP Cache | `<userData>/Cache` |
| VS Code VSIX Cache | `<userData>/CachedExtensionVSIXs` |
| VS Code Stale Workspaces | stale entries in `<userData>/User/workspaceStorage` |
| VS Code Orphaned History | stale entries in `<userData>/User/History` *(opt-in)* |

### VS Code family

Applies to **VS Code**, **VS Code Insiders**, **Cursor**, **VSCodium** and
**Windsurf**, detected automatically. `<userData>` is
`~/Library/Application Support/<app>`.

The webview resource cache (`Service Worker/CacheStorage`) is the item to look at
first. It is never expired automatically, so it can quietly reach tens of GB —
one real machine had **20 GB / 121k files** sitting there untouched since 2024.

## Installation

```bash
npx skills add https://github.com/pipi32167/million-skills --skill clean-my-mac
```

## Usage

Simply ask Claude to clean your Mac:

- "clean my mac"
- "free up disk space"
- "磁盘满了"
- "清理缓存"
- "释放空间"

The skill will:
1. Analyze your disk usage
2. Show a report of what can be cleaned
3. Ask for your confirmation
4. Clean the selected categories
5. Show the results

## Safety

- Always shows analysis before deleting
- Requires user confirmation
- `--dry-run` reports what would be cleaned without touching anything
- Never removes running containers
- Never touches a running VS Code-family editor (skipped and reported)
- Never prunes entries under `/Volumes/*` (drive may just be unmounted)
- Preserves latest Gradle versions
- Local edit history is opt-in only — never part of `all`
