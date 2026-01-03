import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration loader and manager"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default=None):
        """Get config value with dot notation (e.g., 'models.whisper')"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    @property
    def watch_dir(self) -> Path:
        return Path(self.get('watch_directory'))

    @property
    def organized_dir(self) -> Path:
        return Path(self.get('organized_directory'))

    @property
    def use_ai(self) -> bool:
        return self.get('use_ai', True)

    @property
    def confidence_threshold(self) -> float:
        return self.get('confidence_threshold', 0.5)

    @property
    def categories(self) -> Dict[str, list]:
        return self.get('categories', {})
