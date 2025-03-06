import marqo
from typing import List
import logging
from tqdm import tqdm
from .data.data_schema import DatasetMetadata
from .data.utils import load_datasets

# Configure logging for errors only
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_db_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_searchable_content(dataset: DatasetMetadata) -> str:
    return f"""
        Dataset: {dataset['name']}
        Description: {dataset['description']} # An extended description of the dataset (e.g. a readme)
        Modalities: {', '.join(dataset['modalities'])}
        Species: {', '.join(dataset['species'])}
        Tasks: {', '.join(dataset['tasks'])}
        Source: {dataset['source']}
        Data Standard: {dataset['data_standard']}
    """.strip()

def create_marqo_index():
    mq = marqo.Client(url='http://localhost:8882')
    
    # Delete and recreate index
    index_name = "neuroscience_datasets"
    try:
        mq.index(index_name).delete()
    except Exception:
        pass
    
    mq.create_index(index_name, model="hf/e5-base-v2")
    
    # Load datasets
    datasets = load_datasets()
    
    # Convert to Marqo documents and track errors
    documents = []
    for dataset in datasets:
        try:
            doc = {
                **dataset,
                'searchable_content': create_searchable_content(dataset)
            }
            documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset.get('id', 'unknown')}: {str(e)}")
    
    # Index in batches and track errors
    batch_size = 100
    for i in tqdm(range(0, len(documents), batch_size), desc="Indexing documents"):
        batch = documents[i:i+batch_size]
        for doc in batch:
            try:
                mq.index(index_name).add_documents(
                    [doc],  # Index one at a time to isolate errors
                    tensor_fields=["searchable_content", "name", "description"]
                )
            except Exception as e:
                logger.error(f"Failed to index document {doc.get('id', 'unknown')}: {str(e)}")

if __name__ == "__main__":
    create_marqo_index()