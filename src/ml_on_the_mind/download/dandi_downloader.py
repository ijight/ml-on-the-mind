from typing import List
import requests
from tqdm import tqdm
from dandi.dandiapi import DandiAPIClient
from ..data.data_schema import DatasetMetadata
from .base_downloader import DatasetDownloader

class DandiDownloader(DatasetDownloader):
    def __init__(self):
        super().__init__()
        self.client = DandiAPIClient()
        self.output_file = "dandi_datasets.json"
    
    def map_to_common_format(self, dandiset) -> DatasetMetadata:
        try:
            # Get metadata from the dandiset object
            metadata = dandiset.get_raw_metadata()
            
            # Get summary info
            summary = metadata.get('assetsSummary', {})
            
            # Extract species from summary
            species = []
            for species_info in summary.get('species', []):
                if isinstance(species_info, dict) and species_info.get('name'):
                    species.append(species_info['name'])
            
            # Extract modalities from variableMeasured in summary
            modalities = summary.get('variableMeasured', [])
            if not isinstance(modalities, list):
                modalities = []
            
            # Extract measurement techniques from summary
            tasks = []
            for technique in summary.get('measurementTechnique', []):
                if isinstance(technique, dict) and technique.get('name'):
                    tasks.append(technique['name'])
            
            # Get contributors (authors only)
            authors = []
            for contributor in metadata.get('contributor', []):
                if (isinstance(contributor, dict) and 
                    contributor.get('name') and 
                    'dcite:Author' in contributor.get('roleName', [])):
                    authors.append(contributor['name'])
            
            # Get version and construct full ID
            version = metadata.get('version', '')
            dandiset_id = metadata.get('identifier', '').replace('DANDI:', '')
            full_id = f"{dandiset_id}/{version}" if version else dandiset_id
            
            return {
                'id': full_id,
                'name': metadata.get('name', ''),
                'description': metadata.get('description', ''),
                'modalities': modalities,
                'species': species,
                'tasks': tasks,
                'size': summary.get('numberOfBytes', 0),
                'doi': metadata.get('doi', ''),
                'url': metadata.get('url', f"https://dandiarchive.org/dandiset/{full_id}"),
                'source': 'dandi',
                'date_created': metadata.get('dateCreated', ''),
                'authors': authors,
                'license': metadata.get('license', [None])[0],
                'subject_count': summary.get('numberOfSubjects', 0),
                'data_standard': next((std.get('name') for std in summary.get('dataStandard', []) 
                                    if isinstance(std, dict) and std.get('name')), '')
            }
        except Exception as e:
            print(f"Error mapping dandiset {dandiset.identifier}: {str(e)}")
            raise
    
    def fetch_datasets(self) -> List[DatasetMetadata]:
        print("Fetching datasets from DANDI...")
        datasets = []
        
        try:
            # Get all dandisets with progress bar
            dandisets = list(self.client.get_dandisets())
            pbar = tqdm(dandisets, desc="Processing DANDI datasets")
            
            for dandiset in pbar:
                try:
                    # Map to common format
                    dataset = self.map_to_common_format(dandiset)
                    datasets.append(dataset)
                    pbar.set_postfix({'total': len(datasets)})
                    
                except Exception as e:
                    print(f"Error processing dandiset {dandiset.identifier}: {e}")
                    continue
            
            # Save datasets to JSON file
            self.save_datasets(datasets, self.output_file)
            
        except Exception as e:
            print(f"Error fetching DANDI datasets: {e}")
        
        return datasets

if __name__ == "__main__":
    downloader = DandiDownloader()
    datasets = downloader.fetch_datasets()
    print(f"Total DANDI datasets downloaded: {len(datasets)}") 