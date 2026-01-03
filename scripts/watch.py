#!/usr/bin/env python3
"""
Auto-watch mode for continuous organization
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer import FileWatcher, Config

def main():
    # Load configuration
    config = Config()

    # Create and start watcher
    watcher = FileWatcher(config)
    watcher.start()

if __name__ == "__main__":
    main()
