import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class FileDatabase:
    """SQLite database for file indexing"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Force initialization immediately upon creation
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Create the 'files' table
            c.execute('''CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                original_path TEXT,
                mime_type TEXT,
                category TEXT,
                ai_label TEXT,
                confidence REAL,
                size INTEGER,
                created_date TEXT,
                classified_date TEXT,
                metadata TEXT
            )''')

            # Create indexes for speed
            c.execute('''CREATE INDEX IF NOT EXISTS idx_category ON files(category)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_ai_label ON files(ai_label)''')

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ CRITICAL DATABASE ERROR: {e}")
            # If DB is corrupted, we might need to delete it,
            # but for now let's just print the error.

    def insert_file(self, file_data: Dict):
        """Insert or update file record"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Ensure table exists (double-check)
            c.execute('''CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                original_path TEXT,
                mime_type TEXT,
                category TEXT,
                ai_label TEXT,
                confidence REAL,
                size INTEGER,
                created_date TEXT,
                classified_date TEXT,
                metadata TEXT
            )''')

            c.execute('''INSERT OR REPLACE INTO files 
                         (file_path, original_path, mime_type, category, ai_label, 
                          confidence, size, created_date, classified_date, metadata)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (
                          str(file_data['file_path']),
                          str(file_data.get('original_path', '')),
                          file_data.get('mime_type', ''),
                          file_data.get('category', ''),
                          file_data.get('ai_label', ''),
                          file_data.get('confidence', 0.0),
                          file_data.get('size', 0),
                          file_data.get('created_date', ''),
                          datetime.now().isoformat(),
                          json.dumps(file_data.get('metadata', {}))
                      ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Failed to save to DB: {e}")

    def get_stats(self) -> Dict:
        """Get organization statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            if not c.fetchone():
                return {'total_files': 0, 'categories': {}, 'total_size_mb': 0}

            c.execute('SELECT COUNT(*) FROM files')
            total_files = c.fetchone()[0]

            c.execute('SELECT category, COUNT(*) FROM files GROUP BY category')
            category_counts = dict(c.fetchall())

            c.execute('SELECT SUM(size) FROM files')
            result = c.fetchone()[0]
            total_size = result if result else 0

            conn.close()

            return {
                'total_files': total_files,
                'categories': category_counts,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'total_files': 0, 'categories': {}, 'total_size_mb': 0}
