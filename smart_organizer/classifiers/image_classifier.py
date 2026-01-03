import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path
from typing import Dict

from .base_classifier import BaseClassifier

class ImageClassifier(BaseClassifier):
    """Image classification using MediaPipe"""

    def load_model(self):
        """Load MediaPipe image classifier"""
        model_path = self.config.get('models.image_classifier')

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Image model not found: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ImageClassifierOptions(
            base_options=base_options,
            max_results=3
        )

        self.model = vision.ImageClassifier.create_from_options(options)

    def classify(self, file_path: Path) -> Dict[str, any]:
        """Classify an image"""
        if not self.is_loaded():
            self.load_model()

        try:
            image = mp.Image.create_from_file(str(file_path))
            result = self.model.classify(image)

            if result.classifications[0].categories:
                top = result.classifications[0].categories[0]
                all_labels = [
                    {"label": cat.category_name, "score": cat.score}
                    for cat in result.classifications[0].categories
                ]

                return {
                    'label': top.category_name.lower().replace(' ', '_'),
                    'confidence': top.score,
                    'metadata': {'all_predictions': all_labels}
                }
        except Exception as e:
            print(f"Image classification error: {e}")

        return {'label': 'unknown', 'confidence': 0.0}
