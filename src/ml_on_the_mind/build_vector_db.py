import marqo
from typing import List
from tqdm import tqdm
from .data.data_schema import DatasetMetadata
from .data.utils import load_datasets
import os

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

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
    connection_url = "https://74ab-75-50-53-185.ngrok-free.app" # Railway variables are broken worthless peices of shit
    try:
        print(f"Connecting to Marqo at {connection_url}")
        mq = marqo.Client(url=connection_url)
        # Test the connection
        mq.get_indexes()
    except Exception as e:
        print(f"Failed to connect to Marqo at {connection_url}: {str(e)}")
        raise

    print(f"Connected to Marqo at {connection_url}")

    index_name = "neuroscience_datasets"
    try:
        mq.index(index_name).delete()
        print(f"Deleted existing index {index_name}")
    except Exception as e:
        print(f"Could not delete index {index_name}: {str(e)}")

    print(f"Creating index {index_name}")
    mq.create_index(index_name, model="hf/e5-base-v2")
    print(f"Created index {index_name}")

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
            print(f"Failed to process dataset {dataset.get('id', 'unknown')}: {str(e)}")
    
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
                print(f"Failed to index document {doc.get('id', 'unknown')}: {str(e)}")

if __name__ == "__main__":
    create_marqo_index()