"""
Memo-dec: AI Codebase Context Assistant

A command-line tool that creates and maintains intelligent documentation
of software projects to help AI agents and developers understand
codebases more effectively.
"""

__version__ = "0.1.0"
__author__ = "Memo-dec Team"

from .config import Config, ConfigError
from .storage import StorageManager

__all__ = ['Config', 'ConfigError', 'StorageManager']
