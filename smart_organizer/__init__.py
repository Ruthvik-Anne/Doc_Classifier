"""
Smart File Organizer - Intelligent file classification and organization
"""

__version__ = "1.0.0"
__author__ = "Ruthvik Anne"

from .organizer import SmartFileOrganizer
from .watcher import FileWatcher
from .config import Config

__all__ = ["SmartFileOrganizer", "FileWatcher", "Config"]
