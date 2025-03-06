from typing import List
import requests
from tqdm import tqdm
from ..data.data_schema import DatasetMetadata
from .base_downloader import DatasetDownloader

class OpenNeuroDownloader(DatasetDownloader):
    def __init__(self):
        super().__init__()
        self.api_url = "https://openneuro.org/crn/graphql"
        self.output_file = "openneuro_datasets.json"
    
    def map_to_common_format(self, dataset: dict) -> DatasetMetadata:
        metadata = dataset['metadata']
        draft = dataset.get('draft', {})
        
        return {
            'id': metadata['datasetId'],
            'name': metadata['datasetName'],
            'description': draft.get('readme', ''),
            'modalities': metadata.get('modalities', []),
            'species': [metadata.get('species', '')] if metadata.get('species') else [],
            'tasks': metadata.get('tasksCompleted', []),
            'size': draft.get('size', 0),
            'doi': metadata.get('associatedPaperDOI'),
            'url': metadata.get('datasetUrl', ''),
            'source': 'openneuro',
            'date_created': dataset.get('publishDate', ''),
            'authors': [],  # OpenNeuro doesn't provide this in the API
            'license': None  # OpenNeuro doesn't provide this in the API
        }
    
    def fetch_datasets(self) -> List[DatasetMetadata]:
        query = """
            query($after: String, $first: Int = 100) {
                datasets(first: $first, after: $after) {
                    edges {
                        node {
                            metadata {
                                species
                                datasetId
                                datasetName
                                associatedPaperDOI
                                modalities
                                tasksCompleted
                                datasetUrl
                            }
                            name
                            draft {
                                readme
                                size
                            }
                            publishDate
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        """
        
        datasets = []
        has_next_page = True
        after_cursor = None
        
        pbar = tqdm(desc="Fetching OpenNeuro datasets", unit=" datasets")
        
        while has_next_page:
            variables = {
                "first": 100,
                "after": after_cursor
            }
            
            response = requests.post(
                self.api_url,
                json={'query': query, 'variables': variables}
            )
            
            if response.status_code != 200:
                raise Exception(f"Query failed with status code: {response.status_code}")
            
            result = response.json()
            
            if 'data' in result and 'datasets' in result['data']:
                current_datasets = result['data']['datasets']['edges']
                
                # Map each dataset to common format
                mapped_datasets = [
                    self.map_to_common_format(edge['node']) 
                    for edge in current_datasets
                ]
                datasets.extend(mapped_datasets)
                
                page_info = result['data']['datasets']['pageInfo']
                has_next_page = page_info['hasNextPage']
                after_cursor = page_info['endCursor']
                
                pbar.update(len(mapped_datasets))
            else:
                print("No data received in response")
                break
        
        pbar.close()
        
        # Save datasets to JSON file
        self.save_datasets(datasets, self.output_file)
        
        return datasets

if __name__ == "__main__":
    downloader = OpenNeuroDownloader()
    datasets = downloader.fetch_datasets()
    print(f"Total datasets downloaded: {len(datasets)}")