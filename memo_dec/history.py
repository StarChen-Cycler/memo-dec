"""
History management for memo-dec.
Handles versioning and storage of historical symbol and content snapshots.
"""

from pathlib import Path
from datetime import datetime
import json
import shutil


class HistoryManager:
    """
    Manages historical snapshots of symbols and content.

    History is stored in timestamped files:
        .memo/.memosymbols-hist/YYYY-MM-DD_HH-MM-SS.json
        .memo/.memocontent-hist/YYYY-MM-DD_HH-MM-SS.json
    """

    def __init__(self, memo_dir=None):
        """
        Initialize HistoryManager.

        Args:
            memo_dir (Path, optional): Path to .memo directory
        """
        if memo_dir is None:
            self.memo_dir = Path.cwd() / '.memo'
        else:
            self.memo_dir = Path(memo_dir)

        self.symbols_hist_dir = self.memo_dir / '.memosymbols-hist'
        self.content_hist_dir = self.memo_dir / '.memocontent-hist'

    def save_symbol_history(self, symbols, timestamp=None):
        """
        Save symbols to history with timestamp.

        Args:
            symbols (list): List of symbol dictionaries
            timestamp (datetime, optional): Timestamp to use

        Returns:
            Path: Path to saved history file
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Ensure history directory exists
        self.symbols_hist_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        filename = timestamp.strftime('%Y-%m-%d_%H-%M-%S.json')
        history_file = self.symbols_hist_dir / filename

        # Save symbols as JSON
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'timestamp': timestamp.isoformat(),
                    'symbols': symbols,
                    'total_symbols': len(symbols)
                },
                f,
                indent=2,
                ensure_ascii=False
            )

        return history_file

    def save_content_history(self, content, timestamp=None):
        """
        Save content to history with timestamp.

        Args:
            content (dict): Content metadata dictionary
            timestamp (datetime, optional): Timestamp to use

        Returns:
            Path: Path to saved history file
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Ensure history directory exists
        self.content_hist_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        filename = timestamp.strftime('%Y-%m-%d_%H-%M-%SS.json')
        history_file = self.content_hist_dir / filename

        # Save content as JSON
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'timestamp': timestamp.isoformat(),
                    'content': content,
                    'total_files': len(content)
                },
                f,
                indent=2,
                ensure_ascii=False
            )

        return history_file

    def get_symbol_history_files(self):
        """
        Get a list of all symbol history files.

        Returns:
            list[Path]: List of history file paths (sorted by date, newest first)
        """
        if not self.symbols_hist_dir.exists():
            return []

        files = list(self.symbols_hist_dir.glob('*.json'))
        files.sort(reverse=True)  # Sort by filename (timestamp), newest first
        return files

    def get_content_history_files(self):
        """
        Get a list of all content history files.

        Returns:
            list[Path]: List of history file paths (sorted by date, newest first)
        """
        if not self.content_hist_dir.exists():
            return []

        files = list(self.content_hist_dir.glob('*.json'))
        files.sort(reverse=True)  # Sort by filename (timestamp), newest first
        return files

    def load_symbol_history(self, history_file):
        """
        Load symbols from a history file.

        Args:
            history_file (Path): Path to history file

        Returns:
            dict: Dictionary with timestamp, symbols, and total_symbols
        """
        history_file = Path(history_file)

        if not history_file.exists():
            raise FileNotFoundError(f"History file not found: {history_file}")

        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def load_content_history(self, history_file):
        """
        Load content from a history file.

        Args:
            history_file (Path): Path to history file

        Returns:
            dict: Dictionary with timestamp, content, and total_files
        """
        history_file = Path(history_file)

        if not history_file.exists():
            raise FileNotFoundError(f"History file not found: {history_file}")

        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def backup_current_symbols(self, symbols_path):
        """
        Backup current symbols.txt before overwriting it.

        Args:
            symbols_path (Path): Path to current symbols file

        Returns:
            Path or None: Path to backup file
        """
        symbols_path = Path(symbols_path)

        if not symbols_path.exists():
            return None

        # Ensure directory exists
        self.symbols_hist_dir.mkdir(parents=True, exist_ok=True)

        # Create backup filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = self.symbols_hist_dir / f'backup_{timestamp}.txt'

        # Copy current symbols to backup
        shutil.copy2(symbols_path, backup_file)

        return backup_file

    def backup_current_content(self, content_path):
        """
        Backup current content.json before overwriting it.

        Args:
            content_path (Path): Path to current content file

        Returns:
            Path or None: Path to backup file
        """
        content_path = Path(content_path)

        if not content_path.exists():
            return None

        # Ensure directory exists
        self.content_hist_dir.mkdir(parents=True, exist_ok=True)

        # Create backup filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = self.content_hist_dir / f'backup_{timestamp}.json'

        # Copy current content to backup
        shutil.copy2(content_path, backup_file)

        return backup_file

    def delete_old_history(self, keep_count=10):
        """
        Delete old history files, keeping only the most recent ones.

        Args:
            keep_count (int): Number of recent files to keep

        Returns:
            tuple: (deleted_symbols, deleted_content)
        """
        deleted_symbols = 0
        deleted_content = 0

        # Clean symbol history
        symbol_files = self.get_symbol_history_files()
        if len(symbol_files) > keep_count:
            for old_file in symbol_files[keep_count:]:
                old_file.unlink()
                deleted_symbols += 1

        # Clean content history
        content_files = self.get_content_history_files()
        if len(content_files) > keep_count:
            for old_file in content_files[keep_count:]:
                old_file.unlink()
                deleted_content += 1

        return deleted_symbols, deleted_content

    def get_latest_symbol_version(self):
        """
        Get the latest symbol history version.

        Returns:
            Path or None: Path to latest history file or None
        """
        files = self.get_symbol_history_files()
        return files[0] if files else None

    def get_latest_content_version(self):
        """
        Get the latest content history version.

        Returns:
            Path or None: Path to latest history file or None
        """
        files = self.get_content_history_files()
        return files[0] if files else None
