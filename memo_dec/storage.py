"""
Storage management for memo-dec.
Handles creation and management of .memo directory structure.
"""

from pathlib import Path


class StorageManager:
    """
    Manages the .memo directory structure and files.

    Directory structure:
        .memo/
            .memoignore          - Global ignore patterns
            .memoenv             - Configuration file
            memosymbols.txt      - Current symbol documentation
            memocontent.json     - Current content summary
            .memosymbols-hist/   - Symbol history directory
            .memocontent-hist/   - Content history directory
    """

    def __init__(self, project_path=None):
        """
        Initialize StorageManager.

        Args:
            project_path (str or Path, optional): Project root path.
                If None, uses current working directory.
        """
        if project_path is None:
            self.project_path = Path.cwd()
        else:
            self.project_path = Path(project_path)

        self.memo_dir = self.project_path / '.memo'

    def create_memo_dir(self):
        """
        Create the main .memo directory.

        Returns:
            Path: Path to the created directory
        """
        self.memo_dir.mkdir(exist_ok=True)
        return self.memo_dir

    def create_memoignore(self):
        """
        Create default .memoignore file.

        Returns:
            Path: Path to the created file
        """
        memoignore_path = self.memo_dir / '.memoignore'

        # Only create if it doesn't exist
        if not memoignore_path.exists():
            default_patterns = """# Memo-dec Ignore Patterns
# Add files and folders that should not be processed

# Version control
.git
.github
LICENSE
.svn
.hg


# Dependencies and packages
node_modules
venv
env
__pycache__
.pytest_cache

# Build artifacts
build
dist
out
target
*.o
*.so
*.dll
*.exe
*.md

# IDE and editor files
.vscode
.idea
*.swp
*.swo
*~

# Logs and temporary files
*.log
*.tmp
*.temp
*.bak

# OS files
.DS_Store
Thumbs.db
desktop.ini

# Images and binaries (non-code)
*.jpg
*.jpeg
*.png
*.gif
*.svg
*.ico
*.pdf
*.zip
*.tar.gz
*.mp3
*.mp4
*.json
*.txt
*.sh
"""
            with open(memoignore_path, 'w', encoding='utf-8') as f:
                f.write(default_patterns)

        return memoignore_path


    def create_history_dirs(self):
        """
        Create history directories for symbols and content.

        Returns:
            list[Path]: List of created directory paths
        """
        dirs = []

        # Symbol history directory
        symbols_hist_dir = self.memo_dir / '.memosymbols-hist'
        symbols_hist_dir.mkdir(exist_ok=True)
        dirs.append(symbols_hist_dir)

        # Content history directory
        content_hist_dir = self.memo_dir / '.memocontent-hist'
        content_hist_dir.mkdir(exist_ok=True)
        dirs.append(content_hist_dir)

        # Tree storage directory
        tree_dir = self.memo_dir / 'memotree'
        tree_dir.mkdir(exist_ok=True)
        dirs.append(tree_dir)

        return dirs

    def get_memo_dir(self):
        """
        Get the .memo directory path.

        Returns:
            Path: Path to .memo directory
        """
        return self.memo_dir

    def get_memoignore_path(self):
        """
        Get the .memoignore file path.

        Returns:
            Path: Path to .memoignore file
        """
        return self.memo_dir / '.memoignore'

    def get_memoenv_path(self):
        """
        Get the .memoenv file path.

        Returns:
            Path: Path to .memoenv file
        """
        return self.memo_dir / '.memoenv'

    def get_memosymbols_path(self):
        """
        Get the memosymbols.txt file path.

        Returns:
            Path: Path to memosymbols.txt file
        """
        return self.memo_dir / 'memosymbols.txt'

    def get_memocontent_path(self):
        """
        Get the memocontent.json file path.

        Returns:
            Path: Path to memocontent.json file
        """
        return self.memo_dir / 'memocontent.json'

    def get_symbols_hist_dir(self):
        """
        Get the .memosymbols-hist directory path.

        Returns:
            Path: Path to .memosymbols-hist directory
        """
        return self.memo_dir / '.memosymbols-hist'

    def get_content_hist_dir(self):
        """
        Get the .memocontent-hist directory path.

        Returns:
            Path: Path to .memocontent-hist directory
        """
        return self.memo_dir / '.memocontent-hist'

    def get_tree_dir(self):
        """
        Get the memotree directory path.

        Returns:
            Path: Path to memotree directory
        """
        return self.memo_dir / 'memotree'

    def save_tree_files(self, project_path=None):
        """
        Generate and save tree structures to .memo/memotree/.

        Args:
            project_path (Path, optional): Path to project root

        Returns:
            dict: Paths to saved tree files
        """
        from memo_dec import tree_generator

        if project_path is None:
            project_path = self.project_path

        tree_dir = self.get_tree_dir()

        # Get ignore patterns
        ignore_patterns = tree_generator.get_ignore_patterns(project_path)

        # Generate folder-only tree
        folder_tree = tree_generator.generate_tree_structure(
            project_path,
            include_files=False,
            ignore_patterns=ignore_patterns
        )

        # Generate file+folder tree
        file_tree = tree_generator.generate_tree_structure(
            project_path,
            include_files=True,
            ignore_patterns=ignore_patterns
        )

        # Save folder tree
        folder_tree_path = tree_dir / 'memofoldertree.txt'
        with open(folder_tree_path, 'w', encoding='utf-8') as f:
            f.write("# Project Directory Structure (Folders Only)\n")
            f.write("# Generated by memo-dec\n")
            f.write("#\n\n")
            f.write(folder_tree)

        # Save file tree
        file_tree_path = tree_dir / 'memofiletree.txt'
        with open(file_tree_path, 'w', encoding='utf-8') as f:
            f.write("# Project Directory Structure (Folders and Files)\n")
            f.write("# Generated by memo-dec\n")
            f.write("# File sizes are shown in parentheses\n")
            f.write("#\n\n")
            f.write(file_tree)

        return {
            'folder_tree': folder_tree_path,
            'file_tree': file_tree_path
        }

    def initialize_all(self):
        """
        Initialize all memo-dec files and directories.

        Returns:
            dict: Dictionary with paths of created items
        """
        created = {}

        # Create main directory
        created['memo_dir'] = self.create_memo_dir()

        # Create files
        created['memoignore'] = self.create_memoignore()

        # Create directories
        created['history_dirs'] = self.create_history_dirs()

        return created

if __name__ == '__main__':
    # Test storage manager
    storage = StorageManager()
    created = storage.initialize_all()

    print("Created memo-dec structure:")
    for key, value in created.items():
        print(f"  {key}: {value}")
