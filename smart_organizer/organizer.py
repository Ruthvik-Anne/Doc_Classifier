import os
import shutil
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
        mime_type = file_info['mime_type']

        try:
            if self.detector.is_image(mime_type):
                return self.image_classifier.classify(file_path)

            elif self.detector.is_video(mime_type):
                return self.video_classifier.classify(file_path)

            # Pass existing folders for semantic matching
            elif self.detector.is_document(mime_type) or self.get_category_by_extension(file_path) == "Documents":
                existing_folders = self.get_existing_doc_folders()
                return self.document_classifier.classify(file_path, mime_type, existing_folders)

            elif self.detector.is_audio(mime_type):
                return self.audio_classifier.classify(file_path)

        except Exception as e:
            print(f"AI classification error for {file_path.name}: {e}")

        return {'label': 'unknown', 'confidence': 0.0}

    def organize_file(self, file_path: Path, use_ai: bool = None) -> Path:
        if use_ai is None:
            use_ai = self.config.use_ai

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        file_info = self.detector.detect(file_path)
        category = self.get_category_by_extension(file_path)

        ai_result = {'label': 'not_classified', 'confidence': 0.0}
        should_use_ai = use_ai and category in ["Images", "Videos", "Documents", "Audio"]

        if should_use_ai:
            ai_result = self.classify_with_ai(file_path, file_info)

        # Dynamic folder logic for Documents
        if should_use_ai and category == "Documents":
            label = ai_result['label']
            dest_folder = self.organized_dir / category / label
        elif ai_result['confidence'] >= self.config.confidence_threshold:
            dest_folder = self.organized_dir / category / ai_result['label']
        else:
            dest_folder = self.organized_dir / category

        dest_folder.mkdir(parents=True, exist_ok=True)

        # Handle duplicates
        dest_path = dest_folder / file_path.name
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_folder / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        shutil.move(str(file_path), str(dest_path))

        self.db.insert_file({
            'file_path': dest_path,
            'original_path': file_path,
            'mime_type': file_info['mime_type'],
            'category': category,
            'ai_label': ai_result['label'],
            'confidence': ai_result['confidence'],
            'size': os.path.getsize(dest_path),
            'created_date': datetime.fromtimestamp(os.path.getctime(dest_path)).isoformat(),
            'metadata': ai_result.get('metadata', {})
        })

        return dest_path

    def organize_all(self, use_ai: bool = None):
        # Walk through files, ignoring organized directory
        files = []
        for root, _, filenames in os.walk(self.watch_dir):
            if str(self.organized_dir) in root:
                continue
            for filename in filenames:
                file_path = Path(root) / filename
                if not str(file_path).startswith(str(self.organized_dir)):
                    files.append(file_path)

        print(f"\n📁 Found {len(files)} files to organize\n")

        success_count = 0
        for file_path in tqdm(files, desc="Organizing files", unit="file"):
            try:
                new_path = self.organize_file(file_path, use_ai)
                success_count += 1
                if use_ai:
                    try:
                        rel = new_path.relative_to(self.organized_dir)
                    except:
                        rel = new_path.name
                    tqdm.write(f"✓ {file_path.name} → {rel}")
            except Exception as e:
                tqdm.write(f"✗ Error: {file_path.name} - {str(e)}")

        print(f"\n✓ Successfully organized: {success_count} files")
