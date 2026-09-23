#!/usr/bin/env python3
"""
Analyze macOS development cache usage.
Produces a JSON report of cache directories and their sizes.
"""

import json
import os
import subprocess
import urllib.parse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class CacheEntry:
    category_id: str
    name: str
    path: str
    exists: bool
    size_bytes: int
    size_human: str
    count: Optional[int] = None  # e.g., number of dangling volumes
    notes: Optional[str] = None


def human_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_dir_size(path: str) -> int:
    """Get directory size in bytes using du."""
    try:
        result = subprocess.run(
            ['du', '-sk', path],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            # du -sk outputs "size_in_kb\tpath"
            kb = int(result.stdout.split('\t')[0])
            return kb * 1024
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return 0


def get_file_count(path: str) -> int:
    """Get count of items in directory."""
    try:
        result = subprocess.run(
            ['ls', '-1', path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return len(result.stdout.strip().split('\n'))
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return 0


def get_docker_dangling_volumes() -> int:
    """Get count of dangling Docker volumes."""
    try:
        result = subprocess.run(
            ['docker', 'volume', 'ls', '-f', 'dangling=true', '-q'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return len([l for l in lines if l])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 0


def get_docker_disk_usage() -> dict:
    """Get Docker disk usage summary."""
    try:
        result = subprocess.run(
            ['docker', 'system', 'df', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            usage = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        item = json.loads(line)
                        usage[item.get('Type', '').lower()] = item
                    except json.JSONDecodeError:
                        continue
            return usage
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return {}


# Applications that reuse the VS Code / Electron user-data layout.
# (label, user-data directory name under ~/Library/Application Support, .app bundle name)
VSCODE_APPS = [
    ('VS Code', 'Code', 'Visual Studio Code'),
    ('VS Code Insiders', 'Code - Insiders', 'Visual Studio Code - Insiders'),
    ('Cursor', 'Cursor', 'Cursor'),
    ('VSCodium', 'VSCodium', 'VSCodium'),
    ('Windsurf', 'Windsurf', 'Windsurf'),
]

# Cache groups shared by all VS Code-like apps: (category_id, name, relative path, note)
VSCODE_CACHE_GROUPS = [
    (
        'vscode-webview-cache',
        'VS Code Webview Resource Cache',
        Path('Service Worker') / 'CacheStorage',
        'Ephemeral webview/resource cache - rebuilt on demand. Usually the single '
        'biggest reclaimable item, and it never expires on its own.',
    ),
    (
        'vscode-webstorage',
        'VS Code WebStorage',
        Path('WebStorage'),
        'Per-webview CacheStorage + IndexedDB. Safe to drop.',
    ),
    (
        'vscode-http-cache',
        'VS Code HTTP Cache',
        Path('Cache'),
        'Chromium disk HTTP cache.',
    ),
    (
        'vscode-vsix-cache',
        'VS Code Extension VSIX Cache',
        Path('CachedExtensionVSIXs'),
        'Downloaded .vsix installers kept after install. Installed extensions '
        'are unaffected - these are never reused.',
    ),
]


def vscode_app_dirs() -> list:
    """Return [(label, app_bundle_name, user_data_dir)] for installed VS Code-like apps."""
    base = Path.home() / 'Library' / 'Application Support'
    found = []
    for label, dirname, app_name in VSCODE_APPS:
        d = base / dirname
        if d.is_dir():
            found.append((label, app_name, d))
    return found


def is_app_running(app_name: str) -> bool:
    """True if the given .app bundle has a live process."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', f'{app_name}.app/Contents/MacOS'],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip() != ''
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def scan_stale_workspaces(user_dir: Path):
    """Find workspaceStorage entries whose project folder no longer exists.

    Returns (stale_bytes, stale_count, total_count).
    Entries pointing at /Volumes are kept - the drive may simply be unmounted.
    """
    ws = user_dir / 'workspaceStorage'
    if not ws.is_dir():
        return 0, 0, 0

    stale_bytes = stale_count = total_count = 0
    for d in ws.iterdir():
        if not d.is_dir():
            continue
        total_count += 1

        manifest = d / 'workspace.json'
        if not manifest.exists():
            continue
        try:
            folder = json.loads(manifest.read_text()).get('folder', '').replace('file://', '')
            folder = urllib.parse.unquote(folder)
        except Exception:
            continue

        if not folder or os.path.exists(folder) or folder.startswith('/Volumes/'):
            continue

        stale_bytes += get_dir_size(str(d))
        stale_count += 1

    return stale_bytes, stale_count, total_count


def analyze_vscode_apps() -> list[CacheEntry]:
    """Analyse VS Code-family Electron user-data dirs."""
    entries: list[CacheEntry] = []
    apps = vscode_app_dirs()
    if not apps:
        return entries

    running = [label for label, app_name, _ in apps if is_app_running(app_name)]
    warning = f' | ⚠ {running[0]} is RUNNING - close it first' if running else ''

    for cat_id, name, rel, note in VSCODE_CACHE_GROUPS:
        paths, size, count = [], 0, 0
        for _label, _app_name, root in apps:
            p = root / rel
            if p.exists():
                paths.append(p)
                size += get_dir_size(str(p))
                count += get_file_count(str(p))
        if size <= 0:
            continue
        entries.append(CacheEntry(
            category_id=cat_id,
            name=name,
            path=', '.join(str(p) for p in paths),
            exists=True,
            size_bytes=size,
            size_human=human_size(size),
            count=count,
            notes=note + warning,
        ))

    stale_bytes = stale_count = total_count = 0
    for _label, _app_name, root in apps:
        b, s, t = scan_stale_workspaces(root / 'User')
        stale_bytes += b
        stale_count += s
        total_count += t

    if stale_count:
        entries.append(CacheEntry(
            category_id='vscode-stale-workspaces',
            name='VS Code Stale Workspace State',
            path=', '.join(str(root / 'User' / 'workspaceStorage') for _l, _a, root in apps),
            exists=True,
            size_bytes=stale_bytes,
            size_human=human_size(stale_bytes),
            count=stale_count,
            notes=(
                f'{stale_count} of {total_count} workspaces point at folders that no '
                'longer exist. Live workspaces and entries on unmounted /Volumes are kept.'
            ) + warning,
        ))

    return entries


def analyze() -> list[CacheEntry]:
    """Analyze all development caches."""
    entries = []
    home = Path.home()
    
    # === Gradle ===
    gradle_caches = home / '.gradle' / 'caches'
    if gradle_caches.exists():
        entries.append(CacheEntry(
            category_id='gradle-caches',
            name='Gradle Caches',
            path=str(gradle_caches),
            exists=True,
            size_bytes=get_dir_size(str(gradle_caches)),
            size_human=human_size(get_dir_size(str(gradle_caches))),
            notes='All Gradle version caches (safe to delete)'
        ))
    
    gradle_wrapper = home / '.gradle' / 'wrapper' / 'dists'
    if gradle_wrapper.exists():
        entries.append(CacheEntry(
            category_id='gradle-wrapper',
            name='Gradle Wrapper',
            path=str(gradle_wrapper),
            exists=True,
            size_bytes=get_dir_size(str(gradle_wrapper)),
            size_human=human_size(get_dir_size(str(gradle_wrapper))),
            count=get_file_count(str(gradle_wrapper)),
            notes=f'{get_file_count(str(gradle_wrapper))} Gradle versions installed'
        ))
    
    # === Docker ===
    docker_df = get_docker_disk_usage()
    
    if 'local volumes' in docker_df:
        vol_info = docker_df['local volumes']
        reclaimable = vol_info.get('Reclaimable', '0B')
        # Parse reclaimable size
        dangling_count = get_docker_dangling_volumes()
        if dangling_count > 0:
            entries.append(CacheEntry(
                category_id='docker-volumes',
                name='Docker Dangling Volumes',
                path='(docker)',
                exists=True,
                size_bytes=0,  # Would need more parsing
                size_human=reclaimable,
                count=dangling_count,
                notes=f'{dangling_count} dangling volumes'
            ))
    
    if 'images' in docker_df:
        img_info = docker_df['images']
        reclaimable = img_info.get('Reclaimable', '0B')
        if reclaimable != '0B':
            entries.append(CacheEntry(
                category_id='docker-images',
                name='Docker Unused Images',
                path='(docker)',
                exists=True,
                size_bytes=0,
                size_human=reclaimable,
                notes='Unused images'
            ))
    
    # === npm ===
    npm_cache = home / '.npm' / '_cacache'
    if npm_cache.exists():
        entries.append(CacheEntry(
            category_id='npm-cache',
            name='npm Cache',
            path=str(npm_cache),
            exists=True,
            size_bytes=get_dir_size(str(npm_cache)),
            size_human=human_size(get_dir_size(str(npm_cache)))
        ))
    
    # === Yarn ===
    yarn_cache = home / '.cache' / 'yarn'
    if yarn_cache.exists():
        entries.append(CacheEntry(
            category_id='yarn-cache',
            name='Yarn Cache',
            path=str(yarn_cache),
            exists=True,
            size_bytes=get_dir_size(str(yarn_cache)),
            size_human=human_size(get_dir_size(str(yarn_cache)))
        ))
    
    # === pnpm ===
    pnpm_store = home / 'Library' / 'pnpm' / 'store'
    if pnpm_store.exists():
        entries.append(CacheEntry(
            category_id='pnpm-store',
            name='pnpm Store',
            path=str(pnpm_store),
            exists=True,
            size_bytes=get_dir_size(str(pnpm_store)),
            size_human=human_size(get_dir_size(str(pnpm_store)))
        ))
    
    # === Maven ===
    maven_cache = home / '.m2' / 'repository'
    if maven_cache.exists():
        entries.append(CacheEntry(
            category_id='maven-cache',
            name='Maven Repository',
            path=str(maven_cache),
            exists=True,
            size_bytes=get_dir_size(str(maven_cache)),
            size_human=human_size(get_dir_size(str(maven_cache)))
        ))
    
    # === Homebrew ===
    homebrew_cache = home / 'Library' / 'Caches' / 'Homebrew'
    if homebrew_cache.exists():
        entries.append(CacheEntry(
            category_id='homebrew-cache',
            name='Homebrew Cache',
            path=str(homebrew_cache),
            exists=True,
            size_bytes=get_dir_size(str(homebrew_cache)),
            size_human=human_size(get_dir_size(str(homebrew_cache)))
        ))
    
    # === Xcode ===
    xcode_dd = home / 'Library' / 'Developer' / 'Xcode' / 'DerivedData'
    if xcode_dd.exists():
        entries.append(CacheEntry(
            category_id='xcode-deriveddata',
            name='Xcode DerivedData',
            path=str(xcode_dd),
            exists=True,
            size_bytes=get_dir_size(str(xcode_dd)),
            size_human=human_size(get_dir_size(str(xcode_dd)))
        ))
    
    xcode_archives = home / 'Library' / 'Developer' / 'Xcode' / 'Archives'
    if xcode_archives.exists():
        entries.append(CacheEntry(
            category_id='xcode-archives',
            name='Xcode Archives',
            path=str(xcode_archives),
            exists=True,
            size_bytes=get_dir_size(str(xcode_archives)),
            size_human=human_size(get_dir_size(str(xcode_archives)))
        ))
    
    # === VS Code family (Code, Insiders, Cursor, VSCodium, Windsurf) ===
    entries.extend(analyze_vscode_apps())

    return entries


def main():
    """Main entry point."""
    entries = analyze()
    
    total_bytes = sum(e.size_bytes for e in entries)
    
    report = {
        'entries': [asdict(e) for e in entries],
        'total_size_bytes': total_bytes,
        'total_size_human': human_size(total_bytes)
    }
    
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
