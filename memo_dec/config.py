"""
Configuration management for memo-dec.
Handles loading and validation of global .memoenv configuration file.
Based on: @memo-dec/summarize_docs_example.py lines 36-58
"""
import os
from pathlib import Path
from .global_config import GlobalConfigManager


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class Config:
    """
    Configuration class that loads API settings from global .memoenv file.

    Configuration file format (.memoenv):
        API_BASE_URL=https://api.example.com
        API_AUTH_KEY=your_api_key_here
        BATCH_MODEL_NAME=qwen-long-latest
        BATCH_PROCESSING_ENABLED=False

    Global config is located at:
        - Windows: %USERPROFILE%\.memo-dec\.memoenv
        - Linux/macOS: ~/.memo-dec/.memoenv

    Attributes:
        api_base_url (str): URL for the OpenAI-compatible API endpoint
        api_auth_key (str): Authentication key for API access
        batch_model_name (str): Model name for batch processing
        batch_processing_enabled (bool): Whether to use batch mode
    """

    def __init__(self, env_file_path=None):
        """
        Initialize Config by loading .memoenv file.

        Args:
            env_file_path (str or Path, optional): Path to .memoenv file.
                If None, uses global .memo-dec/.memoenv in user's home directory.

        Raises:
            ConfigError: If required configuration is missing or invalid
        """
        self.api_base_url = None
        self.api_auth_key = None
        self.batch_model_name = "qwen-long-latest"
        self.batch_processing_enabled = False

        self.load_env(env_file_path)
        self.validate()

    def load_env(self, env_file_path=None):
        """
        Load configuration from .memoenv file.

        Args:
            env_file_path (str or Path, optional): Path to .memoenv file.
                If None, uses global .memo-dec/.memoenv in user's home directory.
        """
        if env_file_path is None:
            # Use global config in user's home directory
            global_mgr = GlobalConfigManager()
            env_file_path = global_mgr.get_config_file_path()
        else:
            env_file_path = str(env_file_path)

        if not Path(env_file_path).exists():
            raise ConfigError(
                f"Configuration file not found: {env_file_path}\n"
                f"Please run 'memo-dec init --global-config' to create a global configuration file."
            )

        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' not in line:
                            print(f"Warning: Invalid line in config: {line}")
                            continue

                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\"\'')

                        if key == 'API_BASE_URL':
                            self.api_base_url = value
                        elif key == 'API_AUTH_KEY':
                            self.api_auth_key = value
                        elif key == 'BATCH_MODEL_NAME':
                            self.batch_model_name = value
                        elif key == 'BATCH_PROCESSING_ENABLED':
                            self.batch_processing_enabled = value.lower() in ('true', '1', 'yes', 'on')

        except Exception as e:
            raise ConfigError(f"Error reading configuration file: {str(e)}")

    def validate(self):
        """
        Validate that required configuration values are present.

        Raises:
            ConfigError: If required configuration is missing
        """
        missing = []

        if not self.api_base_url:
            missing.append('API_BASE_URL')

        if not self.api_auth_key:
            missing.append('API_AUTH_KEY')

        if missing:
            raise ConfigError(
                f"Missing required configuration values: {', '.join(missing)}\n"
                f"Please add these to your global .memoenv file:\n"
                f"  {GlobalConfigManager().get_config_file_path()}"
            )

    def __str__(self):
        """String representation of config (hiding sensitive data)."""
        return (
            f"Config(\n"
            f"  api_base_url={self.api_base_url},\n"
            f"  api_auth_key=*** (set),\n"
            f"  batch_model_name={self.batch_model_name},\n"
            f"  batch_processing_enabled={self.batch_processing_enabled}\n"
            f")"
        )

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    # Test configuration loading
    try:
        config = Config()
        print("Configuration loaded successfully:")
        print(config)
    except ConfigError as e:
        print(f"Configuration error: {e}")
