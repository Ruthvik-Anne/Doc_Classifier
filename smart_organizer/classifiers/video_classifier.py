import cv2
from pathlib import Path
from typing import Dict

from .image_classifier import ImageClassifier

class VideoClassifier(ImageClassifier):
    """Video classification by sampling frames"""

    def classify(self, file_path: Path) -> Dict[str, any]:
        """Classify video by analyzing sample frames"""
        if not self.is_loaded():
            self.load_model()

        try:
            cap = cv2.VideoCapture(str(file_path))

            if not cap.isOpened():
                return {'label': 'corrupted_video', 'confidence': 0.0}

            # Sample 3 frames: beginning, middle, end
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_positions = [0, total_frames // 2, total_frames - 10]

            labels = []

            for pos in sample_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, pos))
                ret, frame = cap.read()

                if not ret:
                    continue

                # Save temp frame
                temp_path = Path("temp_frame.jpg")
                cv2.imwrite(str(temp_path), frame)

                # Classify frame
                result = super().classify(temp_path)
                labels.append(result['label'])

                temp_path.unlink()

            cap.release()

            # Return most common label
            if labels:
                most_common = max(set(labels), key=labels.count)
                confidence = labels.count(most_common) / len(labels)
                return {'label': most_common, 'confidence': confidence}

        except Exception as e:
            print(f"Video classification error: {e}")

        return {'label': 'unknown_video', 'confidence': 0.0}
