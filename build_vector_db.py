import marqo
import json
import os
from typing import List, Dict
import time

def clean_string(value) -> str:
    """Clean and validate string values"""
    if value is None or value == "" or value == "null":
        return "Not specified"
    return str(value).strip()

def clean_array(value) -> List[str]:
    """Clean and validate array values"""
    if value is None or value == "null":
        return ["Not specified"]
    
    if isinstance(value, str):
        if value.strip() == "" or value.lower() == "null":
            return ["Not specified"]
        return [value.strip()]
    
    if isinstance(value, list):
        # Filter out None, empty strings, "null", etc.
        cleaned = [str(item).strip() for item in value 
                  if item is not None and str(item).strip() != "" 
                  and str(item).lower() not in ["null", "n/a"]]
        return cleaned if cleaned else ["Not specified"]
    
    return ["Not specified"]

def load_json_files(filepath="data/openneuro_datasets.json") -> List[Dict]:
    """Load OpenNeuro datasets from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Transform data into a format suitable for indexing
    documents = []
    for dataset in data:
        # Safely get nested values with defaults
        metadata = dataset.get('metadata', {})
        draft = dataset.get('draft', {})
        
        # Clean and validate all fields
        modalities = clean_array(metadata.get('modalities'))
        tasks = clean_array(metadata.get('tasksCompleted'))
        
        # Ensure all fields have valid string values
        doc = {
            'id': clean_string(metadata.get('datasetId')),
            'name': clean_string(dataset.get('name')),
            'dataset_name': clean_string(metadata.get('datasetName')),
            'species': clean_string(metadata.get('species')),
            'modalities': modalities,
            'doi': clean_string(metadata.get('associatedPaperDOI')),
            'tasks': tasks,
            'url': clean_string(metadata.get('datasetUrl')),
            'readme': clean_string(draft.get('readme')),
            'publish_date': clean_string(dataset.get('publishDate')),
            'size': int(draft.get('size', 0) or 0),  # Handle None/null values for size
            'searchable_content': f"""
                Dataset: {clean_string(metadata.get('datasetName'))}
                Description: {clean_string(draft.get('readme'))}
                Modalities: {', '.join(modalities)}
                Species: {clean_string(metadata.get('species'))}
                Tasks: {', '.join(tasks)}
            """.strip()
        }
        
        documents.append(doc)
    
    print(f"Loaded {len(documents)} valid documents")
    return documents

def batch_documents(documents: List[Dict], batch_size: int = 100) -> List[List[Dict]]:
    """Split documents into batches"""
    return [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]

def create_marqo_index():
    """Create and populate Marqo index"""
    # Initialize Marqo client
    mq = marqo.Client(url='http://localhost:8882')
    
    # Delete existing index if it exists
    index_name = "openneuro_datasets"
    try:
        mq.index(index_name).delete()
        print(f"Deleted existing index: {index_name}")
    except:
        pass
    
    mq.create_index(index_name, model="hf/e5-base-v2")
    print(f"Created new index: {index_name}")
    
    # Load data
    documents = load_json_files()
    
    # Process in batches
    batches = batch_documents(documents, batch_size=100)
    total_docs = len(documents)
    docs_processed = 0
    
    print(f"Processing {total_docs} documents in {len(batches)} batches...")
    
    for i, batch in enumerate(batches, 1):
        try:
            # Specify which fields should be vectorized for searching
            mq.index(index_name).add_documents(
                batch,
                tensor_fields=["searchable_content", "dataset_name", "readme"],  # Don't include array fields
                client_batch_size=20
            )
            docs_processed += len(batch)
            print(f"Batch {i}/{len(batches)} completed. Progress: {docs_processed}/{total_docs} documents")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error processing batch {i}: {e}")
            continue

    print(f"Completed! Added {docs_processed} documents to index")

if __name__ == "__main__":
    create_marqo_index() 