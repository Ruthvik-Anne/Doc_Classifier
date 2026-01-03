import whisper
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path
from typing import Dict

from .base_classifier import BaseClassifier

class AudioClassifier(BaseClassifier):
    """Audio classification using Whisper + sentence transformers"""

    def load_model(self):
        """Load Whisper and sentence transformer models"""
        whisper_model = self.config.get('models.whisper', 'tiny')
        self.whisper_model = whisper.load_model(whisper_model)

        sentence_model = self.config.get('models.sentence_encoder', 'all-MiniLM-L6-v2')
        self.sentence_model = SentenceTransformer(sentence_model)

        # Pre-compute audio type embeddings
        self.audio_types = self.config.get('audio_types', [
            'music', 'podcast', 'lecture', 'phone_call', 'audiobook'
        ])
        self.type_embeddings = self.sentence_model.encode(self.audio_types)

        self.model = True  # Mark as loaded

    def classify(self, file_path: Path) -> Dict[str, any]:
        """Classify audio file"""
        if not self.is_loaded():
            self.load_model()

        try:
            # Transcribe audio
            result = self.whisper_model.transcribe(str(file_path))
            transcript = result["text"]

            if not transcript.strip():
                return {'label': 'silent_audio', 'confidence': 0.0}

            # Classify transcript
            embedding = self.sentence_model.encode([transcript[:1000]])[0]
            similarities = cosine_similarity([embedding], self.type_embeddings)[0]
            best_idx = np.argmax(similarities)

            return {
                'label': self.audio_types[best_idx],
                'confidence': float(similarities[best_idx]),
                'metadata': {'transcript_preview': transcript[:200]}
            }

        except Exception as e:
            print(f"Audio classification error: {e}")

        return {'label': 'unknown_audio', 'confidence': 0.0}
