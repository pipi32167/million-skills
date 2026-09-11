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
- Never removes running containers
- Preserves latest Gradle versions
