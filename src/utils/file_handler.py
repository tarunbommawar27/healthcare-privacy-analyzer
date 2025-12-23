"""File handling utilities"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


class FileHandler:
    """Utility class for file operations"""

    @staticmethod
    def ensure_dir(path: str) -> Path:
        """
        Ensure directory exists, create if it doesn't

        Args:
            path: Directory path

        Returns:
            Path object
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
        """
        Save data to JSON file

        Args:
            data: Data to save
            filepath: Output file path
            indent: JSON indentation
        """
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        """
        Load data from JSON file

        Args:
            filepath: Input file path

        Returns:
            Loaded data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_yaml(filepath: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            filepath: YAML file path

        Returns:
            Configuration dictionary
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def save_text(text: str, filepath: str) -> None:
        """
        Save text to file

        Args:
            text: Text content
            filepath: Output file path
        """
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)

    @staticmethod
    def load_text(filepath: str) -> str:
        """
        Load text from file

        Args:
            filepath: Input file path

        Returns:
            Text content
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def generate_filename(prefix: str, extension: str = "json") -> str:
        """
        Generate timestamped filename

        Args:
            prefix: Filename prefix
            extension: File extension

        Returns:
            Filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
