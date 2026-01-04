import os
import shutil
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from .config import Config
from .file_detector import FileDetector
from .database import FileDatabase
from .classifiers import (
    ImageClassifier,
    VideoClassifier,
    DocumentClassifier,
    AudioClassifier
)


class SmartFileOrganizer:
    """Main file organization orchestrator"""

    def __init__(self, config: Config):
        self.config = config
        self.watch_dir = config.watch_dir
        self.organized_dir = config.organized_dir
        self.organized_dir.mkdir(exist_ok=True, parents=True)

        # Initialize components
        self.detector = FileDetector()
        self.db = FileDatabase(self.organized_dir / "file_index.db")

        # Initialize classifiers (lazy loading)
        self.image_classifier = ImageClassifier(config)
        self.video_classifier = VideoClassifier(config)
        self.document_classifier = DocumentClassifier(config)
        self.audio_classifier = AudioClassifier(config)

    def get_category_by_extension(self, file_path: Path) -> str:
        """Get category based on file extension"""
        ext = file_path.suffix.lower().replace('.', '')

        for category, extensions in self.config.categories.items():
            if ext in extensions:
                return category

        return "Others"

    def get_existing_doc_folders(self) -> list:
        """Scan document folders to provide context to AI"""
        doc_path = self.organized_dir / "Documents"
        if not doc_path.exists():
            return []
        return [d.name for d in doc_path.iterdir() if d.is_dir()]

    def classify_with_ai(self, file_path: Path, file_info: dict) -> dict:
        """Route to appropriate AI classifier"""
        mime_type = file_info['mime_type']

        try:
            if self.detector.is_image(mime_type):
                return self.image_classifier.classify(file_path)

            elif self.detector.is_video(mime_type):
                return self.video_classifier.classify(file_path)

            # Pass existing folders for semantic matching to DocumentClassifier
            elif self.detector.is_document(mime_type) or self.get_category_by_extension(file_path) == "Documents":
                existing_folders = self.get_existing_doc_folders()
                return self.document_classifier.classify(file_path, mime_type, existing_folders)

            elif self.detector.is_audio(mime_type):
                return self.audio_classifier.classify(file_path)

        except Exception as e:
            print(f"AI classification error for {file_path.name}: {e}")

        return {'label': 'unknown', 'confidence': 0.0}

    def organize_file(self, file_path: Path, use_ai: bool = None) -> Path:
        """Organize a single file with Retry Logic for locked files."""
        if use_ai is None:
            use_ai = self.config.use_ai

        # --- RETRY LOGIC START ---
        # Waits up to 3 seconds for file to unlock (fix for errno=2 / PermissionError)
        retries = 3
        while retries > 0:
            if not file_path.exists():
                # File disappeared (e.g. temp file deleted by system)
                return None

            try:
                # Test if we can actually open the file
                with open(file_path, 'rb') as f:
                    pass
                break  # Success! File is readable.
            except (PermissionError, OSError):
                time.sleep(1)  # Wait 1 second
                retries -= 1

        if retries == 0:
            tqdm.write(f"🔒 Skipped locked file: {file_path.name}")
            return None
        # --- RETRY LOGIC END ---

        # Detect file type
        file_info = self.detector.detect(file_path)
        category = self.get_category_by_extension(file_path)

        ai_result = {'label': 'not_classified', 'confidence': 0.0}

        # Determine if we should use AI based on category
        should_use_ai = use_ai and category in ["Images", "Videos", "Documents", "Audio"]

        if should_use_ai:
            ai_result = self.classify_with_ai(file_path, file_info)

        # Determine Destination Folder
        dest_folder = self.organized_dir / category

        if should_use_ai:
            # For Documents: Use the AI label as the subfolder (Dynamic Creation)
            if category == "Documents":
                label = ai_result['label']
                dest_folder = dest_folder / label

            # For Others (Images/Audio): Use label only if high confidence
            elif ai_result['confidence'] >= self.config.confidence_threshold:
                dest_folder = dest_folder / ai_result['label']

        dest_folder.mkdir(parents=True, exist_ok=True)

        # Handle duplicate filenames
        dest_path = dest_folder / file_path.name
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_folder / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        # Move the file
        try:
            shutil.move(str(file_path), str(dest_path))
        except OSError as e:
            tqdm.write(f"❌ Move failed for {file_path.name}: {e}")
            return None

        # Record in Database
        try:
            self.db.insert_file({
                'file_path': dest_path,
                'original_path': file_path,
                'mime_type': file_info['mime_type'],
                'category': category,
                'ai_label': ai_result['label'],
                'confidence': ai_result['confidence'],
                'size': os.path.getsize(dest_path),
                'created_date': datetime.now().isoformat(),
                'metadata': ai_result.get('metadata', {})
            })
        except Exception:
            # Don't crash organization if logging fails
            pass

        return dest_path

    def organize_all(self, use_ai: bool = None):
        """Organize files IN-PLACE, skipping already organized category folders."""
        files = []

        print(f"🔍 Scanning: {self.watch_dir}")

        # Define the category folders we create (to skip them)
        # These are the top-level folders defined in config.yaml
        category_folders = list(self.config.categories.keys()) + ["Others", "Unreadable_Docs"]

        for root, dirs, filenames in os.walk(self.watch_dir):
            root_path = Path(root)

            # 1. SKIP LOGIC: Check if we are inside a Category Folder
            # Calculate path relative to the main watch dir
            try:
                rel_path = root_path.relative_to(self.watch_dir)
                # If the first part of the path is a known category (e.g. "Downloads/Images"), skip it
                if str(rel_path) != "." and rel_path.parts[0] in category_folders:
                    continue
            except ValueError:
                pass  # Should not happen if root is inside watch_dir

            for filename in filenames:
                file_path = root_path / filename

                # Skip hidden files
                if filename.startswith('.'): continue

                # Skip the database file itself
                if filename == "file_index.db": continue

                files.append(file_path)

        if not files:
            print("✨ No unorganized files found! (Or folder is empty)")
            return

        print(f"\n📁 Found {len(files)} loose files. Organizing...\n")

        success_count = 0
        error_count = 0

        for file_path in tqdm(files, desc="Organizing", unit="file"):
            try:
                # organize_file uses self.organized_dir, which we set to match watch_dir
                # So it will move "Downloads/file.pdf" -> "Downloads/Documents/Label/file.pdf"
                new_path = self.organize_file(file_path, use_ai)
                if new_path:
                    success_count += 1
            except Exception as e:
                error_count += 1
                tqdm.write(f"✗ Error: {file_path.name} - {e}")

        # Cleanup empty folders (OPTIONAL - Be careful with in-place!)
        # self.remove_empty_folders()
        # I disabled this by default for In-Place mode to avoid deleting user's custom empty folders.

        print(f"\n{'=' * 60}")
        print(f"✓ Organized: {success_count} files")
        print(f"{'=' * 60}\n")

    def remove_empty_folders(self):
        """Delete empty subfolders after files have been moved out"""
        # Walk bottom-up so we can delete nested empty folders
        for root, dirs, files in os.walk(self.watch_dir, topdown=False):
            root_path = Path(root)

            # Skip output dir
            try:
                if self.organized_dir.resolve() in root_path.resolve().parents or self.organized_dir.resolve() == root_path.resolve():
                    continue
            except:
                if str(self.organized_dir) in str(root_path):
                    continue

            # Don't delete the main watch dir itself
            if root_path.resolve() == self.watch_dir.resolve():
                continue

            # If empty, delete
            if not any(root_path.iterdir()):
                try:
                    root_path.rmdir()
                except OSError:
                    pass
