#!/usr/bin/env python3
"""
Search organized files
"""

import sys
from pathlib import Path
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smart_organizer import Config
from smart_organizer.database import FileDatabase

def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Load config
    config = Config()

    # Search database
    db = FileDatabase(config.organized_dir / "file_index.db")
    results = db.search(query)

    if not results:
        print(f"\n❌ No files found for query: '{query}'")
        return

    # Format results
    table_data = []
    for r in results:
        file_name = Path(r['file_path']).name
        table_data.append([
            file_name[:40],
            r['category'],
            r['ai_label'],
            f"{r['confidence']:.2f}",
            r['classified_date'][:10]
        ])

    print(f"\n🔍 Search results for: '{query}'")
    print(f"Found {len(results)} files\n")

    print(tabulate(
        table_data,
        headers=['File Name', 'Category', 'AI Label', 'Confidence', 'Date'],
        tablefmt='grid'
    ))

if __name__ == "__main__":
    main()
