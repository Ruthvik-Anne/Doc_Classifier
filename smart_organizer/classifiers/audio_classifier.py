import whisper
from sentence_transformers import SentenceTransformer, util
import torch
import shutil
import time
from pathlib import Path
from typing import Dict

from .base_classifier import BaseClassifier


class AudioClassifier(BaseClassifier):
    """Audio classification using Whisper + sentence transformers"""

    def load_model(self):
        """Load Whisper and sentence transformer models"""
        # Check for FFmpeg first
        if not shutil.which("ffmpeg"):
            print("❌ Error: FFmpeg not found. Audio classification will be disabled.")
            print("   Install FFmpeg: https://ffmpeg.org/download.html")
            self.model = None
            return

        try:
            print("🎤 Loading Whisper Model...")
            whisper_model_name = self.config.get('models.whisper', 'tiny')
            self.whisper_model = whisper.load_model(whisper_model_name)

            print("🧠 Loading Audio Semantic Engine...")
            sentence_model_name = self.config.get('models.sentence_encoder', 'all-MiniLM-L6-v2')
            self.sentence_model = SentenceTransformer(sentence_model_name)

            # Define base categories with descriptive terms
            self.audio_types = [
                'music song band artist album',
                'podcast interview episode discussion',
                'lecture class tutorial education',
                'voice_memo meeting recording',
                'audiobook chapter narration'
            ]
            self.type_embeddings = self.sentence_model.encode(self.audio_types, convert_to_tensor=True)
            self.model = True

        except Exception as e:
            print(f"❌ Failed to load audio models: {e}")
            self.model = None

    def classify(self, file_path: Path) -> Dict[str, any]:
        """Classify audio file with robust retry logic"""
        if self.model is None:
            self.load_model()
            if self.model is None:
                return {'label': 'Unclassified_Audio', 'confidence': 0.0}

        # AGGRESSIVE RETRY LOGIC
        # Try up to 5 times with increasing wait times
        max_retries = 5
        wait_times = [0.5, 1, 2, 3, 5]  # seconds

        for attempt in range(max_retries):
            try:
                # Test file accessibility
                if not file_path.exists():
                    return {'label': 'File_Not_Found', 'confidence': 0.0}

                # Try to open and read first byte to ensure file is readable
                with open(file_path, 'rb') as f:
                    f.read(1)

                # If we got here, file is accessible, try Whisper transcription
                # fp16=False is crucial for CPU, language=None for auto-detect
                result = self.whisper_model.transcribe(
                    str(file_path),
                    fp16=False,
                    language=None,
                    verbose=False  # Suppress Whisper's output
                )

                transcript = result["text"].strip()

                # If no speech detected (instrumental music, noise)
                if len(transcript) < 5:
                    return {'label': 'Music', 'confidence': 0.5}

                # Classify the transcript
                embedding = self.sentence_model.encode(transcript, convert_to_tensor=True)
                cosine_scores = util.cos_sim(embedding, self.type_embeddings)[0]

                best_idx = int(torch.argmax(cosine_scores))
                best_score = float(cosine_scores[best_idx])

                # Extract category name (first word of description)
                category_name = self.audio_types[best_idx].split(' ')[0].capitalize()

                return {
                    'label': category_name,
                    'confidence': best_score,
                    'metadata': {'transcript_preview': transcript[:100]}
                }

            except FileNotFoundError:
                # File disappeared completely
                return {'label': 'File_Not_Found', 'confidence': 0.0}

            except (PermissionError, OSError) as e:
                # File is locked or inaccessible
                if attempt < max_retries - 1:
                    # Wait and retry
                    time.sleep(wait_times[attempt])
                    continue
                else:
                    # Final attempt failed
                    # print(f"⚠️ Audio locked after {max_retries} attempts: {file_path.name}")
                    return {'label': 'Music', 'confidence': 0.3}

            except Exception as e:
                # Any other error (corrupted file, unsupported format, etc.)
                # print(f"⚠️ Audio processing error: {e}")
                return {'label': 'Unknown_Audio', 'confidence': 0.0}

        # Should never reach here, but just in case
        return {'label': 'Unknown_Audio', 'confidence': 0.0}
