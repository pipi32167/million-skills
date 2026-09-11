#!/usr/bin/env python3
"""
Analyze macOS development cache usage.
Produces a JSON report of cache directories and their sizes.
"""

import json
import os
import subprocess
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
            timeout=30
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
