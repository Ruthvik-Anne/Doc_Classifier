#!/usr/bin/env python3
"""
One-time file organization script
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer import SmartFileOrganizer, Config

def main():
    print("\n" + "="*60)
    print("Smart File Organizer - One-time Organization")
    print("="*60 + "\n")

    # Load configuration
    config = Config()

    # Create organizer
    organizer = SmartFileOrganizer(config)

    # Ask user for AI mode
    use_ai = input("Use AI classification? (slower but smarter) [Y/n]: ").strip().lower()
    use_ai = use_ai != 'n'

    # Organize all files
    organizer.organize_all(use_ai=use_ai)

if __name__ == "__main__":
    main()
