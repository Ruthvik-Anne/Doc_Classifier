import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .organizer import SmartFileOrganizer
from .config import Config

class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""

    def __init__(self, organizer: SmartFileOrganizer, config: Config):
        self.organizer = organizer
        self.config = config
        self.ignore_patterns = config.get('watcher.ignore_patterns', [])
        self.debounce = config.get('watcher.debounce_seconds', 2)
        self.pending_files = {}

    def should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if file_path.name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if file_path.name.startswith(pattern[:-1]):
                    return True
            elif pattern in str(file_path):
                return True

        return False

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if self.should_ignore(file_path):
            return

        # Debounce: wait for file to finish copying
        time.sleep(self.debounce)

        if not file_path.exists():
            return

        print(f"\n🆕 New file detected: {file_path.name}")

        try:
            new_path = self.organizer.organize_file(file_path, use_ai=True)
            print(f"✓ Organized to: {new_path.relative_to(self.organizer.organized_dir)}")

        except Exception as e:
            print(f"✗ Error organizing {file_path.name}: {e}")

class FileWatcher:
    """File system watcher"""

    def __init__(self, config: Config):
        self.config = config
        self.organizer = SmartFileOrganizer(config)
        self.observer = Observer()

    def start(self):
        """Start watching directory"""
        event_handler = FileEventHandler(self.organizer, self.config)

        watch_dir = str(self.config.watch_dir)
        recursive = self.config.get('watcher.recursive', True)

        self.observer.schedule(event_handler, watch_dir, recursive=recursive)
        self.observer.start()

        print(f"\n{'='*60}")
        print(f"👀 Watching: {watch_dir}")
        print(f"📂 Organizing to: {self.config.organized_dir}")
        print(f"🤖 AI Classification: {'Enabled' if self.config.use_ai else 'Disabled'}")
        print(f"{'='*60}")
        print("\nPress Ctrl+C to stop...\n")

        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching"""
        self.observer.stop()
        self.observer.join()
        print("\n\n✓ Watcher stopped")
