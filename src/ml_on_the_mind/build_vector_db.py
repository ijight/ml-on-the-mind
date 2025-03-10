import marqo
from typing import List
import logging
from tqdm import tqdm
from .data.data_schema import DatasetMetadata
from .data.utils import load_datasets
import os
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
        Description: {dataset['description']}
        Modalities: {', '.join(dataset['modalities'])}
        Species: {', '.join(dataset['species'])}
        Tasks: {', '.join(dataset['tasks'])}
        Source: {dataset['source']}
        Data Standard: {dataset['data_standard']}
    """.strip()

def create_marqo_index():
    connection_url = os.getenv("MARQO_URL", "http://localhost:8882")
    try:
        print(f"Connecting to Marqo at {connection_url}")
        mq = marqo.Client(url=connection_url)
        # Test the connection
        mq.get_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to Marqo at {connection_url}: {str(e)}")
        raise

    print(f"Connected to Marqo at {connection_url}")

    index_name = "neuroscience_datasets"
    try:
        mq.index(index_name).delete()
        print(f"Deleted existing index {index_name}")
    except Exception as e:
        logger.warning(f"Could not delete index {index_name}: {str(e)}")
    
    try:
        print(f"Creating index {index_name}")
        settings = {
            "treat_urls_and_pointers_as_images": False,
            "model": "hf/e5-base-v2"
        }
        mq.create_index(index_name, settings_dict=settings)
        print(f"Created index {index_name}")
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        raise

    datasets = load_datasets()
    
    print(f"Loaded {len(datasets)} datasets")

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
    
    print(f"Indexing {len(documents)} documents")

    batch_size = 100
    for i in tqdm(range(0, len(documents), batch_size), desc="Indexing documents"):
        batch = documents[i:i+batch_size]
        for doc in batch:
            try:
                mq.index(index_name).add_documents(
                    [doc],
                    tensor_fields=["searchable_content", "name", "description"]
                )
            except Exception as e:
                logger.error(f"Failed to index document {doc.get('id', 'unknown')}: {str(e)}")

if __name__ == "__main__":
    create_marqo_index()