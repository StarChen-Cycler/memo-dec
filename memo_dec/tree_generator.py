"""
Tree Generator Module for Memo-Dec

Generates project structure trees for analysis and AI-powered ignore file generation.
"""

import os
from typing import List, Tuple, Optional
from pathlib import Path


def format_file_size(size: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


def generate_tree_structure(
    path: str,
    include_files: bool = True,
    max_depth: Optional[int] = None,
    ignore_patterns: Optional[List[str]] = None
) -> str:
    """
    Generate a hierarchical tree structure of the directory.

    Args:
        path: Root path to generate tree from
        include_files: Whether to include files in the tree output
        max_depth: Maximum depth to traverse (None for unlimited)
        ignore_patterns: List of glob patterns to ignore

    Returns:
        String representation of the tree structure
    """
    def should_ignore(item_path: str, is_dir: bool) -> bool:
        """Check if path should be ignored based on patterns."""
        if not ignore_patterns:
            return False

        rel_path = os.path.relpath(item_path, path)
        if rel_path == '.':
            return False

        # Check against each pattern
        for pattern in ignore_patterns:
            # Handle directory pattern (ends with /)
            if pattern.endswith('/') and is_dir:
                dir_pattern = pattern.rstrip('/')
                if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                    return True
            # Handle file/directory name pattern
            elif not pattern.endswith('/'):
                import fnmatch
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                    return True

        return False

    def walk_directory(current_path: str, prefix: str = '', depth: int = 0) -> List[str]:
        """Recursively walk directory and build tree lines."""
        if max_depth is not None and depth > max_depth:
            return []

        lines = []
        try:
            items = sorted(os.listdir(current_path))
        except (PermissionError, OSError):
            return [f"{prefix}[Permission Denied]"]

        # Separate directories and files
        dirs = []
        files = []

        for item in items:
            item_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(item_path)

            if should_ignore(item_path, is_dir):
                continue

            if is_dir:
                dirs.append(item)
            elif include_files:
                files.append(item)

        # Process directories
        for i, dir_name in enumerate(dirs):
            item_path = os.path.join(current_path, dir_name)
            is_last = (i == len(dirs) - 1) and (not include_files or not files)

            connector = '└── ' if is_last else '├── '
            lines.append(f"{prefix}{connector}{dir_name}/")

            new_prefix = prefix + ('    ' if is_last else '│   ')
            lines.extend(walk_directory(item_path, new_prefix, depth + 1))

        # Process files
        if include_files:
            for i, file_name in enumerate(files):
                item_path = os.path.join(current_path, file_name)
                is_last = i == len(files) - 1

                connector = '└── ' if is_last else '├── '
                if include_files:
                    try:
                        size = os.path.getsize(item_path)
                        size_str = format_file_size(size)
                        lines.append(f"{prefix}{connector}{file_name} ({size_str})")
                    except (OSError, IOError):
                        lines.append(f"{prefix}{connector}{file_name}")
                else:
                    lines.append(f"{prefix}{connector}{file_name}")

        return lines

    # Get the root directory name
    root_name = os.path.basename(os.path.abspath(path))
    tree_lines = [f"{root_name}/"]
    tree_lines.extend(walk_directory(path))

    return '\n'.join(tree_lines)


def get_ignore_patterns(project_path: str) -> List[str]:
    """
    Load ignore patterns from .memo/.memoignore file.

    Args:
        project_path: Path to project root

    Returns:
        List of ignore patterns
    """
    ignore_file = os.path.join(project_path, '.memo', '.memoignore')
    patterns = []

    if os.path.exists(ignore_file):
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)

    return patterns


def get_directory_info(path: str) -> Tuple[int, int, int]:
    """
    Get statistics about a directory.

    Args:
        path: Path to directory

    Returns:
        Tuple of (total_files, total_dirs, total_size_bytes)
    """
    total_files = 0
    total_dirs = 0
    total_size = 0

    for root, dirs, files in os.walk(path):
        total_dirs += len(dirs)
        total_files += len(files)
        for file in files:
            try:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
            except (OSError, IOError):
                pass

    return total_files, total_dirs, total_size


def is_large_project(path: str, file_threshold: int = 1000, size_threshold_mb: int = 50) -> bool:
    """
    Determine if a project is "large" based on file count and total size.

    Args:
        path: Path to project root
        file_threshold: Number of files that constitutes "large"
        size_threshold_mb: Size in MB that constitutes "large"

    Returns:
        True if project is considered large
    """
    total_files, _, total_size = get_directory_info(path)
    size_mb = total_size / (1024 * 1024)

    return total_files > file_threshold or size_mb > size_threshold_mb
