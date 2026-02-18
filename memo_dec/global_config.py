"""
Global Configuration Manager for Memo-Dec

Handles global .memoenv file in user's home directory.
"""

import os
from pathlib import Path


class GlobalConfigManager:
    """
    Manages the global .memo-dec configuration directory.

    Global config location depends on OS:
    - Windows: %USERPROFILE%\.memo-dec\.memoenv
    - Linux/macOS: ~/.memo-dec/.memoenv
    """

    def __init__(self):
        """Initialize GlobalConfigManager."""
        self.config_dir = self._get_global_config_dir()
        self.config_file = self.config_dir / '.memoenv'

    def _get_global_config_dir(self) -> Path:
        """
        Get the global configuration directory path.

        Returns:
            Path: Path to global .memo-dec directory
        """
        # Use user's home directory
        home_dir = Path.home()
        return home_dir / '.memo-dec'

    def ensure_config_dir(self) -> Path:
        """
        Ensure the global configuration directory exists.

        Returns:
            Path: Path to the created/existing directory
        """
        self.config_dir.mkdir(exist_ok=True)
        return self.config_dir

    def create_global_memoenv(self) -> Path:
        """
        Create global .memoenv file if it doesn't exist.

        Returns:
            Path: Path to the created/existing config file
        """
        self.ensure_config_dir()

        if not self.config_file.exists():
            template = """# Memo-Dec Global Configuration File
# This file contains API credentials and settings used by all projects

# Required: API base URL for OpenAI-compatible API
API_BASE_URL= "https://api.example.com"

# Required: API authentication key
API_AUTH_KEY="your_api_key_here"

# Optional: Model name for batch processing (default: qwen-long-latest)
BATCH_MODEL_NAME="qwen-long-latest"

# Optional: Enable batch processing (default: False)
BATCH_PROCESSING_ENABLED=False

# Optional: Maximum tokens for API responses
# MAX_TOKENS=4000

# Optional: Temperature for AI responses (0.0-1.0)
# TEMPERATURE=0.3
"""
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(template)

        return self.config_file

    def get_config_file_path(self) -> str:
        """
        Get the global config file path.

        Returns:
            str: Path to global .memoenv file as string
        """
        return str(self.config_file)

    def config_exists(self) -> bool:
        """
        Check if global config file exists.

        Returns:
            bool: True if config file exists
        """
        return self.config_file.exists()

    def delete_config(self):
        """
        Delete the global configuration file and directory.

        Returns:
            bool: True if deletion successful
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            if self.config_dir.exists() and not any(self.config_dir.iterdir()):
                self.config_dir.rmdir()
            return True
        except Exception:
            return False
