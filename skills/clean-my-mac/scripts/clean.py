#!/usr/bin/env python3
"""
Clean macOS development caches.
Executes cleanup based on selected categories.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CleanResult:
    category_id: str
    name: str
    success: bool
    size_freed: int
    size_freed_human: str
    message: Optional[str] = None


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
            timeout=30
        )
        if result.returncode == 0:
            kb = int(result.stdout.split('\t')[0])
            return kb * 1024
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return 0


def remove_directory(path: Path) -> bool:
    """Remove a directory safely."""
    try:
        if path.exists():
            shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"Error removing {path}: {e}", file=sys.stderr)
    return False


def clean_gradle_caches() -> CleanResult:
    """Clean all Gradle caches."""
    path = Path.home() / '.gradle' / 'caches'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    if path.exists():
        success = remove_directory(path)
        return CleanResult(
            category_id='gradle-caches',
            name='Gradle Caches',
            success=success,
            size_freed=size,
            size_freed_human=human_size(size)
        )
    return CleanResult(
        category_id='gradle-caches',
        name='Gradle Caches',
        success=True,
        size_freed=0,
        size_freed_human='0 B',
        message='Directory not found'
    )


def clean_gradle_wrapper(keep_latest: int = 1) -> CleanResult:
    """Clean old Gradle wrapper versions, keeping latest N."""
    dists_path = Path.home() / '.gradle' / 'wrapper' / 'dists'
    
    if not dists_path.exists():
        return CleanResult(
            category_id='gradle-wrapper',
            name='Gradle Wrapper',
            success=True,
            size_freed=0,
            size_freed_human='0 B',
            message='Directory not found'
        )
    
    # Get all version directories
    versions = []
    for item in dists_path.iterdir():
        if item.is_dir():
            versions.append((item, item.stat().st_mtime))
    
    # Sort by modification time (newest first)
    versions.sort(key=lambda x: x[1], reverse=True)
    
    # Remove old versions
    total_freed = 0
    removed = 0
    
    for path, _ in versions[keep_latest:]:
        size = get_dir_size(str(path))
        if remove_directory(path):
            total_freed += size
            removed += 1
    
    return CleanResult(
        category_id='gradle-wrapper',
        name='Gradle Wrapper',
        success=True,
        size_freed=total_freed,
        size_freed_human=human_size(total_freed),
        message=f'Removed {removed} old versions, kept {keep_latest}'
    )


def clean_docker_volumes() -> CleanResult:
    """Clean dangling Docker volumes."""
    try:
        # Get size before cleanup
        result = subprocess.run(
            ['docker', 'system', 'df', '-v', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Run volume prune
        result = subprocess.run(
            ['docker', 'volume', 'prune', '-f'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Parse "Total reclaimed space: X.XXGB" from output
            for line in result.stdout.split('\n'):
                if 'Total reclaimed space' in line:
                    size_str = line.split(':')[-1].strip()
                    return CleanResult(
                        category_id='docker-volumes',
                        name='Docker Dangling Volumes',
                        success=True,
                        size_freed=0,  # Would need proper parsing
                        size_freed_human=size_str
                    )
            
            return CleanResult(
                category_id='docker-volumes',
                name='Docker Dangling Volumes',
                success=True,
                size_freed=0,
                size_freed_human='0 B',
                message='No dangling volumes found'
            )
    except Exception as e:
        return CleanResult(
            category_id='docker-volumes',
            name='Docker Dangling Volumes',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_docker_images() -> CleanResult:
    """Clean unused Docker images."""
    try:
        result = subprocess.run(
            ['docker', 'image', 'prune', '-f'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Total reclaimed space' in line:
                    size_str = line.split(':')[-1].strip()
                    return CleanResult(
                        category_id='docker-images',
                        name='Docker Unused Images',
                        success=True,
                        size_freed=0,
                        size_freed_human=size_str
                    )
            
            return CleanResult(
                category_id='docker-images',
                name='Docker Unused Images',
                success=True,
                size_freed=0,
                size_freed_human='0 B',
                message='No unused images found'
            )
    except Exception as e:
        return CleanResult(
            category_id='docker-images',
            name='Docker Unused Images',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_npm_cache() -> CleanResult:
    """Clean npm cache."""
    path = Path.home() / '.npm' / '_cacache'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    try:
        result = subprocess.run(
            ['npm', 'cache', 'clean', '--force'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return CleanResult(
            category_id='npm-cache',
            name='npm Cache',
            success=result.returncode == 0,
            size_freed=size,
            size_freed_human=human_size(size),
            message=result.stderr if result.returncode != 0 else None
        )
    except Exception as e:
        return CleanResult(
            category_id='npm-cache',
            name='npm Cache',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_yarn_cache() -> CleanResult:
    """Clean Yarn cache."""
    path = Path.home() / '.cache' / 'yarn'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    try:
        result = subprocess.run(
            ['yarn', 'cache', 'clean'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return CleanResult(
            category_id='yarn-cache',
            name='Yarn Cache',
            success=result.returncode == 0,
            size_freed=size,
            size_freed_human=human_size(size),
            message=result.stderr if result.returncode != 0 else None
        )
    except Exception as e:
        return CleanResult(
            category_id='yarn-cache',
            name='Yarn Cache',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_pnpm_store() -> CleanResult:
    """Clean pnpm store."""
    path = Path.home() / 'Library' / 'pnpm' / 'store'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    try:
        result = subprocess.run(
            ['pnpm', 'store', 'prune'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return CleanResult(
            category_id='pnpm-store',
            name='pnpm Store',
            success=result.returncode == 0,
            size_freed=size,
            size_freed_human=human_size(size),
            message=result.stderr if result.returncode != 0 else None
        )
    except Exception as e:
        return CleanResult(
            category_id='pnpm-store',
            name='pnpm Store',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_maven_cache() -> CleanResult:
    """Clean Maven repository."""
    path = Path.home() / '.m2' / 'repository'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    if path.exists():
        success = remove_directory(path)
        return CleanResult(
            category_id='maven-cache',
            name='Maven Repository',
            success=success,
            size_freed=size,
            size_freed_human=human_size(size)
        )
    return CleanResult(
        category_id='maven-cache',
        name='Maven Repository',
        success=True,
        size_freed=0,
        size_freed_human='0 B',
        message='Directory not found'
    )


def clean_homebrew_cache() -> CleanResult:
    """Clean Homebrew cache."""
    path = Path.home() / 'Library' / 'Caches' / 'Homebrew'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    try:
        result = subprocess.run(
            ['brew', 'cleanup', '--prune=all'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return CleanResult(
            category_id='homebrew-cache',
            name='Homebrew Cache',
            success=result.returncode == 0,
            size_freed=size,
            size_freed_human=human_size(size),
            message=result.stderr if result.returncode != 0 else None
        )
    except Exception as e:
        return CleanResult(
            category_id='homebrew-cache',
            name='Homebrew Cache',
            success=False,
            size_freed=0,
            size_freed_human='0 B',
            message=str(e)
        )


def clean_xcode_deriveddata() -> CleanResult:
    """Clean Xcode DerivedData."""
    path = Path.home() / 'Library' / 'Developer' / 'Xcode' / 'DerivedData'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    if path.exists():
        success = remove_directory(path)
        return CleanResult(
            category_id='xcode-deriveddata',
            name='Xcode DerivedData',
            success=success,
            size_freed=size,
            size_freed_human=human_size(size)
        )
    return CleanResult(
        category_id='xcode-deriveddata',
        name='Xcode DerivedData',
        success=True,
        size_freed=0,
        size_freed_human='0 B',
        message='Directory not found'
    )


def clean_xcode_archives() -> CleanResult:
    """Clean Xcode Archives."""
    path = Path.home() / 'Library' / 'Developer' / 'Xcode' / 'Archives'
    size = get_dir_size(str(path)) if path.exists() else 0
    
    if path.exists():
        success = remove_directory(path)
        return CleanResult(
            category_id='xcode-archives',
            name='Xcode Archives',
            success=success,
            size_freed=size,
            size_freed_human=human_size(size)
        )
    return CleanResult(
        category_id='xcode-archives',
        name='Xcode Archives',
        success=True,
        size_freed=0,
        size_freed_human='0 B',
        message='Directory not found'
    )


# Applications that reuse the VS Code / Electron user-data layout.
VSCODE_APPS = [
    ('VS Code', 'Code', 'Visual Studio Code'),
    ('VS Code Insiders', 'Code - Insiders', 'Visual Studio Code - Insiders'),
    ('Cursor', 'Cursor', 'Cursor'),
    ('VSCodium', 'VSCodium', 'VSCodium'),
    ('Windsurf', 'Windsurf', 'Windsurf'),
]

# Purely regenerable caches: rendered content is re-fetched on demand.
VSCODE_CACHE_GROUPS = {
    'vscode-webview-cache': ('VS Code Webview Resource Cache', Path('Service Worker') / 'CacheStorage'),
    'vscode-webstorage': ('VS Code WebStorage', Path('WebStorage')),
    'vscode-http-cache': ('VS Code HTTP Cache', Path('Cache')),
    'vscode-vsix-cache': ('VS Code Extension VSIX Cache', Path('CachedExtensionVSIXs')),
}

# Destructive / data-loss categories - never included in `all`.
OPT_IN_CATEGORIES = {'vscode-history-orphaned'}


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


def empty_dir_contents(path: Path) -> None:
    """Delete everything inside path, keeping the directory itself."""
    for item in path.iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass


def _clean_vscode_cache(category_id: str) -> CleanResult:
    """Empty one regenerable cache group across every installed VS Code-like app.

    Never touches an app that is currently running: Electron holds those files
    open and would rewrite them on exit anyway.
    """
    name, rel = VSCODE_CACHE_GROUPS[category_id]
    freed = 0
    cleaned, running, errors = [], [], []

    for label, app_name, root in vscode_app_dirs():
        target = root / rel
        if not target.exists():
            continue
        if is_app_running(app_name):
            running.append(label)
            continue
        size = get_dir_size(str(target))
        try:
            target.mkdir(parents=True, exist_ok=True)
            empty_dir_contents(target)
            freed += size
            cleaned.append(f'{label} ({human_size(size)})')
        except Exception as e:
            errors.append(f'{label}: {e}')

    if not cleaned and not running and not errors:
        return CleanResult(category_id, name, True, 0, '0 B', 'Nothing to clean')

    message = []
    if cleaned:
        message.append('cleaned ' + ', '.join(cleaned))
    if running:
        message.append('skipped (app running): ' + ', '.join(running))
    if errors:
        message.append('errors: ' + '; '.join(errors))

    return CleanResult(
        category_id=category_id,
        name=name,
        success=not errors and not running,
        size_freed=freed,
        size_freed_human=human_size(freed),
        message=' | '.join(message),
    )


def clean_vscode_webview_cache() -> CleanResult:
    return _clean_vscode_cache('vscode-webview-cache')


def clean_vscode_webstorage() -> CleanResult:
    return _clean_vscode_cache('vscode-webstorage')


def clean_vscode_http_cache() -> CleanResult:
    return _clean_vscode_cache('vscode-http-cache')


def clean_vscode_vsix_cache() -> CleanResult:
    return _clean_vscode_cache('vscode-vsix-cache')


def _scan_stale_workspaces():
    """Find workspaceStorage dirs whose recorded project folder no longer exists.

    Returns (targets, kept, running) where targets is [(path, size_bytes)].
    Live projects, entries without a workspace.json, and paths under /Volumes
    (the drive may simply be unmounted) are counted as kept.
    """
    targets, kept, running = [], 0, []
    for label, app_name, root in vscode_app_dirs():
        ws = root / 'User' / 'workspaceStorage'
        if not ws.is_dir():
            continue
        if is_app_running(app_name):
            running.append(label)
            continue

        for d in sorted(ws.iterdir()):
            if not d.is_dir():
                continue
            manifest = d / 'workspace.json'
            if not manifest.exists():
                kept += 1
                continue
            try:
                folder = json.loads(manifest.read_text()).get('folder', '').replace('file://', '')
                folder = urllib.parse.unquote(folder)
            except Exception:
                kept += 1
                continue

            if not folder or os.path.exists(folder) or folder.startswith('/Volumes/'):
                kept += 1
                continue

            targets.append((d, get_dir_size(str(d))))

    return targets, kept, running


def _scan_orphaned_history():
    """Find local-history dirs whose source file no longer exists.

    Returns (targets, kept, running) where targets is [(path, size_bytes)].
    """
    targets, kept, running = [], 0, []
    for label, app_name, root in vscode_app_dirs():
        history = root / 'User' / 'History'
        if not history.is_dir():
            continue
        if is_app_running(app_name):
            running.append(label)
            continue

        for d in sorted(history.iterdir()):
            if not d.is_dir():
                continue
            manifest = d / 'entries.json'
            if not manifest.exists():
                kept += 1
                continue
            try:
                resource = json.loads(manifest.read_text()).get('resource', '')
                resource = urllib.parse.unquote(resource.replace('file://', ''))
            except Exception:
                kept += 1
                continue

            if not resource or os.path.exists(resource) or resource.startswith('/Volumes/'):
                kept += 1
                continue

            targets.append((d, get_dir_size(str(d))))

    return targets, kept, running


def clean_vscode_stale_workspaces() -> CleanResult:
    """Remove workspaceStorage entries whose project folder no longer exists."""
    targets, kept, running = _scan_stale_workspaces()

    freed, removed, errors = 0, 0, []
    for path, size in targets:
        try:
            shutil.rmtree(path)
            freed += size
            removed += 1
        except Exception as e:
            errors.append(f'{path.name}: {e}')

    message = f'removed {removed} stale workspaces, kept {kept}'
    if running:
        message += ' | skipped (app running): ' + ', '.join(running)
    if errors:
        message += ' | errors: ' + '; '.join(errors[:5])

    return CleanResult(
        category_id='vscode-stale-workspaces',
        name='VS Code Stale Workspace State',
        success=not errors and not running,
        size_freed=freed,
        size_freed_human=human_size(freed),
        message=message,
    )


def clean_vscode_history_orphaned() -> CleanResult:
    """Remove local edit-history dirs whose source file no longer exists.

    OPT-IN only: VS Code's local history is a data store, not a cache. History
    for files that still exist is preserved, so undo-over-time keeps working.
    """
    targets, kept, running = _scan_orphaned_history()

    freed, removed, errors = 0, 0, []
    for path, size in targets:
        try:
            shutil.rmtree(path)
            freed += size
            removed += 1
        except Exception as e:
            errors.append(f'{path.name}: {e}')

    message = f'removed {removed} orphaned history entries, kept {kept}'
    if running:
        message += ' | skipped (app running): ' + ', '.join(running)
    if errors:
        message += ' | errors: ' + '; '.join(errors[:5])

    return CleanResult(
        category_id='vscode-history-orphaned',
        name='VS Code Orphaned Local History',
        success=not errors and not running,
        size_freed=freed,
        size_freed_human=human_size(freed),
        message=message,
    )


# Category handler mapping
CLEANERS = {
    'gradle-caches': clean_gradle_caches,
    'gradle-wrapper': clean_gradle_wrapper,
    'docker-volumes': clean_docker_volumes,
    'docker-images': clean_docker_images,
    'npm-cache': clean_npm_cache,
    'yarn-cache': clean_yarn_cache,
    'pnpm-store': clean_pnpm_store,
    'maven-cache': clean_maven_cache,
    'homebrew-cache': clean_homebrew_cache,
    'xcode-deriveddata': clean_xcode_deriveddata,
    'xcode-archives': clean_xcode_archives,
    'vscode-webview-cache': clean_vscode_webview_cache,
    'vscode-webstorage': clean_vscode_webstorage,
    'vscode-http-cache': clean_vscode_http_cache,
    'vscode-vsix-cache': clean_vscode_vsix_cache,
    'vscode-stale-workspaces': clean_vscode_stale_workspaces,
    'vscode-history-orphaned': clean_vscode_history_orphaned,
}

# `all` = every regenerable category; destructive ones stay opt-in only.
ALL_CATEGORIES = [c for c in CLEANERS if c not in OPT_IN_CATEGORIES]


def main():
    parser = argparse.ArgumentParser(description='Clean macOS development caches')
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=list(CLEANERS.keys()) + ['all'],
        default=['all'],
        help='Categories to clean (default: all)'
    )
    parser.add_argument(
        '--keep-latest',
        type=int,
        default=1,
        help='Number of Gradle versions to keep (default: 1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned without actually cleaning'
    )
    
    args = parser.parse_args()
    
    # Determine categories to clean
    if 'all' in args.categories:
        categories = list(ALL_CATEGORIES)
    else:
        categories = [c for c in args.categories if c != 'all']
    
    results = []

    if args.dry_run:
        # Report what would be cleaned without touching anything.
        scanners = {
            'vscode-stale-workspaces': _scan_stale_workspaces,
            'vscode-history-orphaned': _scan_orphaned_history,
        }

        for category in categories:
            if category in VSCODE_CACHE_GROUPS:
                name, rel = VSCODE_CACHE_GROUPS[category]
            else:
                name, rel = category, None

            if rel is not None:
                size, targets = 0, []
                for _label, _app, root in vscode_app_dirs():
                    p = root / rel
                    if p.exists():
                        size += get_dir_size(str(p))
                        targets.append(str(p))
                detail = '; '.join(targets) if targets else 'nothing found'

            elif category in scanners:
                found, kept, running = scanners[category]()
                size = sum(s for _p, s in found)
                detail = f'{len(found)} entries, {kept} kept'
                if running:
                    detail += ' (app running: ' + ', '.join(running) + ')'

            else:
                size, detail = 0, 'n/a - run without --dry-run to clean'

            results.append(CleanResult(
                category_id=category,
                name=name,
                success=True,
                size_freed=size,
                size_freed_human=human_size(size),
                message=f'DRY RUN would clean {detail}',
            ))
    else:
        for category in categories:
            print(f"Cleaning {category}...", file=sys.stderr)

            # Special handling for gradle-wrapper with keep_latest
            if category == 'gradle-wrapper':
                result = clean_gradle_wrapper(keep_latest=args.keep_latest)
            else:
                result = CLEANERS[category]()

            results.append(result)
    
    # Output results as JSON
    output = {
        'dry_run': args.dry_run,
        'results': [
            {
                'category_id': r.category_id,
                'name': r.name,
                'success': r.success,
                'size_freed_human': r.size_freed_human,
                'message': r.message
            }
            for r in results
        ]
    }
    
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
