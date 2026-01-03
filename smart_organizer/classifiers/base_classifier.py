from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

class BaseClassifier(ABC):
    """Abstract base class for all classifiers"""

    def __init__(self, config):
        self.config = config
        self.model = None

    @abstractmethod
    def load_model(self):
        """Load the AI model"""
        pass

    @abstractmethod
    def classify(self, file_path: Path) -> Dict[str, any]:
        """
        Classify a file and return result

        Returns:
        {
          'label': str,
          'confidence': float,
          'metadata': dict (optional)
        }
        """
        pass

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
