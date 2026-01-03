import magic
from pathlib import Path
from typing import Dict

class FileDetector:
    """Detect file types using magic bytes"""

    def __init__(self):
        self.mime_detector = magic.Magic(mime=True)
        self.desc_detector = magic.Magic()

    def detect(self, file_path: Path) -> Dict[str, str]:
        """Detect file type and return MIME type + description"""
        try:
            return {
                "mime_type": self.mime_detector.from_file(str(file_path)),
                "description": self.desc_detector.from_file(str(file_path)),
                "extension": file_path.suffix.lower().replace('.', '')
            }
        except Exception as e:
            return {
                "mime_type": "application/octet-stream",
                "description": f"Error: {str(e)}",
                "extension": file_path.suffix.lower().replace('.', '')
            }

    def is_image(self, mime_type: str) -> bool:
        return mime_type.startswith("image/")

    def is_video(self, mime_type: str) -> bool:
        return mime_type.startswith("video/")

    def is_audio(self, mime_type: str) -> bool:
        return mime_type.startswith("audio/")

    def is_document(self, mime_type: str) -> bool:
        return (mime_type == "application/pdf" or
                "wordprocessingml" in mime_type or
                "text/" in mime_type)
