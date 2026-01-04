#!/usr/bin/env python3
"""
Interactive In-Place File Organizer
Organizes files directly inside the source folder.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer import SmartFileOrganizer, Config


def get_valid_path(prompt, default_path):
    while True:
        user_input = input(f"{prompt} [{default_path}]: ").strip()
        path = Path(default_path) if not user_input else Path(user_input)

        if not path.exists():
            print(f"❌ Error: Path does not exist: {path}")
        else:
            return path


def main():
    print("\n" + "=" * 60)
    print(" 📂  SMART FILE ORGANIZER - IN-PLACE MODE")
    print("=" * 60 + "\n")

    # 1. Load defaults
    try:
        config = Config()
        default_watch = config.watch_dir
    except:
        default_watch = Path.home() / "Downloads"

    # 2. Ask User
    print("--- Configuration ---")
    watch_dir = get_valid_path("Folder to Organize", default_watch)

    use_ai_input = input("Use AI Classification? [Y/n]: ").strip().lower()
    use_ai = use_ai_input != 'n'

    print("\n" + "-" * 60)
    print(f"🚀 Organizing inside: {watch_dir}")
    print(f"   (Folders will be created directly in this folder)")
    print("-" * 60)

    if input("\nStart? (Enter/q): ").lower() == 'q': return

    # 3. Configure for In-Place
    # Set organized_dir SAME as watch_dir
    config.config['watch_directory'] = str(watch_dir)
    config.config['organized_directory'] = str(watch_dir)
    config.config['use_ai'] = use_ai

    # 4. Run
    organizer = SmartFileOrganizer(config)
    organizer.organize_all(use_ai=use_ai)


if __name__ == "__main__":
    main()
