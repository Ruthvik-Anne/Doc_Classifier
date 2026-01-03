import fitz  # PyMuPDF
from docx import Document
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
import re
import torch
import numpy as np
from typing import Dict, List, Tuple

from .base_classifier import BaseClassifier


class DocumentClassifier(BaseClassifier):
    """
    Advanced Document Classifier with Multi-Keyword Extraction & Semantic Matching.
    Extracts multiple diverse topics and semantically matches them to existing folders.
    """

    def load_model(self):
        # We need both KeyBERT for extraction and SentenceTransformer for comparison
        model_name = self.config.get('models.sentence_encoder', 'all-MiniLM-L6-v2')
        print(f"🧠 Loading Advanced Semantic Topic Engine ({model_name})...")

        # Load shared model to save RAM
        self.encoder = SentenceTransformer(model_name)
        # KeyBERT uses the encoder we just loaded
        self.kw_model = KeyBERT(model=self.encoder)
        self.model = True

    def extract_text(self, file_path: Path, mime_type: str) -> str:
        text = ""
        try:
            if mime_type == "application/pdf":
                doc = fitz.open(file_path)
                # Read first 10 pages for deeper context
                text = "\n".join([page.get_text() for page in doc[:10]])
                doc.close()
            elif "wordprocessingml" in mime_type:
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs[:150]])
            elif mime_type.startswith("text/") or str(file_path).endswith(('.epub', '.mobi')):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(15000)
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
        return text

    def clean_filename(self, name: str) -> str:
        # Title case and remove illegal chars
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().title()

    def find_best_existing_folder(self, candidates: List[str], existing_folders: List[str]) -> Tuple[str, float]:
        """
        Compare a list of candidate topics against all existing folders.
        Returns (best_folder_name, match_score).
        """
        if not existing_folders or not candidates:
            return None, 0.0

        # Encode candidates and folders
        # candidates_emb shape: [num_candidates, 384]
        candidates_emb = self.encoder.encode(candidates, convert_to_tensor=True)
        # folder_emb shape: [num_folders, 384]
        folder_emb = self.encoder.encode(existing_folders, convert_to_tensor=True)

        # Calculate cosine similarity matrix [num_candidates, num_folders]
        cosine_scores = util.cos_sim(candidates_emb, folder_emb)

        # Find the single best match across all combinations
        best_score = float(torch.max(cosine_scores))

        # Get indices of the best match
        # argmax returns flat index, we need to unravel it (or just use simple numpy logic if easier)
        # Here we iterate to find exactly which pair it was for clarity
        best_candidate_idx, best_folder_idx = np.unravel_index(
            torch.argmax(cosine_scores).cpu().numpy(),
            cosine_scores.shape
        )

        return existing_folders[best_folder_idx], best_score

    def classify(self, file_path: Path, mime_type: str = None, existing_folders: List[str] = None) -> Dict[str, any]:
        if not self.is_loaded():
            self.load_model()

        text = self.extract_text(file_path, mime_type or "application/pdf")

        if len(text.strip()) < 50:
            return {'label': 'Unreadable_Docs', 'confidence': 0.0}

        # 1. Extract MULTIPLE diverse keywords
        # use_mmr=True ensures we get distinct topics, not just variations of the same word
        # diversity=0.3 allows some variation but keeps them relevant
        keywords_data = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),  # Allow longer phrases like "Harry Potter Series"
            stop_words='english',
            use_mmr=True,
            diversity=0.3,
            top_n=3
        )

        if not keywords_data:
            return {'label': 'General_Docs', 'confidence': 0.0}

        # Extract just the strings from the tuples [('topic', 0.9), ...]
        candidate_topics = [k[0] for k in keywords_data]
        top_score = keywords_data[0][1]  # Score of the very best keyword

        print(f"   🔍 Candidates for '{file_path.name}': {candidate_topics}")

        # 2. SEMANTIC MATCHING against existing folders
        if existing_folders:
            best_folder, match_score = self.find_best_existing_folder(candidate_topics, existing_folders)

            # If match is strong (> 0.65), merge into that folder
            if match_score > 0.65:
                print(f"   🔄 Merging into '{best_folder}' (Score: {match_score:.2f})")
                return {'label': best_folder, 'confidence': float(match_score)}

        # 3. Create NEW folder if no match
        # Use the first (best) candidate as the new folder name
        new_folder = self.clean_filename(candidate_topics[0])
        return {'label': new_folder, 'confidence': float(top_score)}
