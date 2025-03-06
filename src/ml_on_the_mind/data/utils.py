import json
import os
from typing import List, Dict
from .data_schema import DatasetMetadata

def clean_string(value: str) -> str:
    """Clean and standardize string values"""
    if value is None or value == "" or str(value).lower() in ["null", "n/a", "none"]:
        return "Not specified"
    return str(value).strip()

def clean_array(value: List[str]) -> List[str]:
    """Clean and standardize array values"""
    if not value:
        return ["Not specified"]
    
    cleaned = [
        str(item).strip() 
        for item in value 
        if item is not None and str(item).strip() and str(item).lower() not in ["null", "n/a", "none"]
    ]
    return cleaned if cleaned else ["Not specified"]

def clean_dataset(dataset: Dict) -> DatasetMetadata:
    """Clean a single dataset entry"""
    return {
        'id': clean_string(dataset.get('id')),
        'name': clean_string(dataset.get('name')),
        'description': clean_string(dataset.get('description')),
        'modalities': clean_array(dataset.get('modalities', [])),
        'species': clean_array(dataset.get('species', [])),
        'tasks': clean_array(dataset.get('tasks', [])),
        'size': int(dataset.get('size', 0) or 0),
        'doi': clean_string(dataset.get('doi')),
        'url': clean_string(dataset.get('url')),
        'source': clean_string(dataset.get('source')),
        'date_created': clean_string(dataset.get('date_created')),
        'authors': clean_array(dataset.get('authors', [])),
        'license': clean_string(dataset.get('license')),
        'subject_count': int(dataset.get('subject_count', 0) or 0),
        'data_standard': clean_string(dataset.get('data_standard'))
    }

def load_datasets(data_dir: str = "cache") -> List[DatasetMetadata]:
    """Load and clean all dataset JSON files from data directory"""
    all_datasets = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith('_datasets.json'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    datasets = json.load(f)
                cleaned_datasets = [clean_dataset(d) for d in datasets]
                all_datasets.extend(cleaned_datasets)
                print(f"Loaded {len(cleaned_datasets)} datasets from {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    print(f"Total datasets loaded: {len(all_datasets)}")
    return all_datasets 