"""
File monitoring for memo-dec.
Monitors project directory for changes using hash-based detection.
Based on: @memo-dec/summarize_docs_example.py lines 252-268, 276-369
"""

import os
import hashlib
import time
from pathlib import Path
import fnmatch


class FileMonitor:
    """
    Monitors a project directory and tracks file changes using hash-based detection.

    Computes MD5 hashes of files to detect new, modified, and deleted files.
    Respects ignore patterns from .memo/.memoignore.
    """

    def __init__(self, project_path=None, memo_dir=None):
        """
        Initialize FileMonitor.

        Args:
            project_path (Path, optional): Path to project root
            memo_dir (Path, optional): Path to .memo directory
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.memo_dir = memo_dir or (self.project_path / '.memo')

        # Load ignore patterns
        self.ignore_patterns = self._load_ignore_patterns()

    def _load_ignore_patterns(self):
        """
        Load ignore patterns from .memo/.memoignore file.

        Returns:
            list: List of glob patterns to ignore
        """
        ignore_file = self.memo_dir / '.memoignore'
        patterns = []

        if ignore_file.exists():
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                print(f"Warning: Could not read .memoignore: {e}")

        return patterns

    def should_ignore(self, path):
        """
        Check if a file or directory should be ignored.

        Args:
            path (Path): Path to check

        Returns:
            bool: True if path should be ignored
        """
        rel_path = path.relative_to(self.project_path) if path.is_absolute() else path
        rel_path_str = str(rel_path)

        # Check patterns against path
        for pattern in self.ignore_patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                # Match files inside the directory: pattern* (e.g., .memo/*)
                dir_pattern = pattern.rstrip('/') + '/*'
                # Or match the directory itself
                dir_self = pattern.rstrip('/')

                if fnmatch.fnmatch(rel_path_str, dir_pattern):
                    return True
                if fnmatch.fnmatch(rel_path_str, dir_self):
                    return True
                if fnmatch.fnmatch(path.name, dir_self):
                    return True

                # Check if path is inside the directory
                rel_path_parts = rel_path_str.split('/')
                dir_parts = dir_self.split('/')
                if len(rel_path_parts) >= len(dir_parts) and rel_path_parts[:len(dir_parts)] == dir_parts:
                    return True

                # Check if any parent matches the directory
                for parent in rel_path.parents:
                    if str(parent) == dir_self:
                        return True
            else:
                # Regular file pattern
                if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                    return True

                # Check if any parent directory matches
                for parent in rel_path.parents:
                    if fnmatch.fnmatch(str(parent), pattern):
                        return True

        return False

    def calculate_file_hash(self, file_path):
        """
        Calculate MD5 hash of a file.

        Args:
            file_path (Path): Path to file

        Returns:
            str: Hex digest of MD5 hash
        """
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def scan_project(self, calculate_hashes=True):
        """
        Scan the project directory and collect file information.

        Args:
            calculate_hashes (bool): Whether to calculate file hashes

        Returns:
            dict: Dictionary with file paths as keys and file info as values
        """
        file_info = {}

        # Walk through directory
        for root, dirs, files in os.walk(self.project_path):
            root_path = Path(root)

            # Filter out directories that should be ignored
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]

            for file in files:
                file_path = root_path / file

                # Skip files that should be ignored
                if self.should_ignore(file_path):
                    continue

                # Skip the metadata file itself
                if os.path.abspath(file_path) == os.path.abspath(self.memo_dir / 'memocontent.json'):
                    continue

                rel_path = file_path.relative_to(self.project_path)
                info = {
                    'path': file_path,
                    'relative_path': str(rel_path),
                    'last_modified': file_path.stat().st_mtime,
                }

                if calculate_hashes:
                    try:
                        info['hash'] = self.calculate_file_hash(file_path)
                    except Exception as e:
                        print(f"Warning: Could not hash {file_path}: {e}")
                        info['hash'] = None

                file_info[str(rel_path)] = info

        return file_info

    def find_changed_files(self, old_metadata, new_metadata):
        """
        Compare old and new metadata to find changed files.

        Args:
            old_metadata (dict): Previous file metadata
            new_metadata (dict): Current file metadata

        Returns:
            dict: Dictionary with changed files categorized as new, modified, deleted
        """
        if not old_metadata:
            # If no previous metadata, all files are new
            return {
                'new': list(new_metadata.keys()),
                'modified': [],
                'deleted': [],
                'unchanged': []
            }

        new_files = []
        modified_files = []
        deleted_files = []
        unchanged_files = []

        # Check for new and modified files
        for rel_path, new_info in new_metadata.items():
            if rel_path not in old_metadata:
                new_files.append(rel_path)
            elif old_metadata[rel_path].get('hash') != new_info.get('hash'):
                modified_files.append(rel_path)
            else:
                unchanged_files.append(rel_path)

        # Check for deleted files
        for rel_path in old_metadata:
            if rel_path not in new_metadata:
                deleted_files.append(rel_path)

        return {
            'new': new_files,
            'modified': modified_files,
            'deleted': deleted_files,
            'unchanged': unchanged_files
        }

    def get_changed_files(self, metadata=None):
        """
        Get list of changed files since last scan.

        Args:
            metadata (dict, optional): Previously saved metadata

        Returns:
            dict: Dictionary with categories of changed files
        """
        # Scan current project
        current_metadata = self.scan_project(calculate_hashes=True)

        # Find changes
        changes = self.find_changed_files(metadata or {}, current_metadata)

        return changes

    def filter_by_extensions(self, file_info, extensions):
        """
        Filter file info by extensions.

        Args:
            file_info (dict): File information dictionary
            extensions (list): List of file extensions to include

        Returns:
            dict: Filtered file information
        """
        if not extensions:
            return file_info

        filtered = {}
        for rel_path, info in file_info.items():
            if any(rel_path.endswith(ext) for ext in extensions):
                filtered[rel_path] = info

        return filtered

    def filter_by_size(self, file_info, max_size_mb=10):
        """
        Filter out files larger than max_size_mb.

        Args:
            file_info (dict): File information dictionary
            max_size_mb (int): Maximum file size in MB

        Returns:
            dict: Filtered file information
        """
        max_bytes = max_size_mb * 1024 * 1024
        filtered = {}

        for rel_path, info in file_info.items():
            file_path = info['path']
            try:
                if file_path.stat().st_size <= max_bytes:
                    filtered[rel_path] = info
            except Exception as e:
                print(f"Warning: Could not check size of {file_path}: {e}")

        return filtered

    def has_file_changed(self, metadata, rel_path, file_hash):
        """
        Check if a file has changed based on hash.

        Args:
            metadata (dict): Metadata dictionary
            rel_path (str): Relative path to file
            file_hash (str): Current file hash

        Returns:
            bool: True if file is new or has changed
        """
        if rel_path not in metadata:
            return True

        old_hash = metadata[rel_path].get('hash')
        return old_hash != file_hash

    def get_supported_files(self):
        """
        Get only files with supported extensions for symbol extraction.

        Returns:
            dict: File information for supported files
        """
        all_files = self.scan_project(calculate_hashes=False)

        supported_extensions = ['.py', '.js', '.ts', '.tsx', '.c', '.cpp', '.cc', '.h',
                                 '.java', '.md', '.html', '.htm', '.json']

        return self.filter_by_extensions(all_files, supported_extensions)


if __name__ == '__main__':
    # Test file monitor
    monitor = FileMonitor()
    print("Scanning project...")
    files = monitor.scan_project()
    print(f"Found {len(files)} files")

    # Show first 5 files
    for i, rel_path in enumerate(list(files.keys())[:5]):
        info = files[rel_path]
        print(f"  {rel_path}: {len(info.get('hash', ''))} chars hash")
