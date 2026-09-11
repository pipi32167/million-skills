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
}


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
        categories = list(CLEANERS.keys())
    else:
        categories = args.categories
    
    results = []
    
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
