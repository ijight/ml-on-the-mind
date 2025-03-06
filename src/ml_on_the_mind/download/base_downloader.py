from abc import ABC, abstractmethod
from typing import List
import json
import os
from ..data.data_schema import DatasetMetadata

class DatasetDownloader(ABC):
    def __init__(self):
        self.data_dir = "cache"
        os.makedirs(self.data_dir, exist_ok=True)
    
    @abstractmethod
    def fetch_datasets(self) -> List[DatasetMetadata]:
        """Fetch datasets and return in common format"""
        pass
    
    @abstractmethod
    def map_to_common_format(self, dataset: dict) -> DatasetMetadata:
        """Map repository-specific format to common format"""
        pass
    
    def save_datasets(self, datasets: List[DatasetMetadata], filename: str):
        """Save datasets to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(datasets, f, indent=2)
        print(f"Saved {len(datasets)} datasets to {filepath}") 