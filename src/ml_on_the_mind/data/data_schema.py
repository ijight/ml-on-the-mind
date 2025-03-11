from typing import List, TypedDict, Optional, Union
from datetime import datetime

class DatasetMetadata(TypedDict):
    """Unified schema for a searchable dataset. 
    I'm not actually using this right now, but it's here for reference.

        Args:
            id: str                     # Unique identifier
            name: str                   # Dataset name
            description: str            # Full description/readme
            modalities: List[str]       # Imaging/recording modalities
            species: List[str]         # Study species
            tasks: List[str]           # Experimental tasks
            size: int                  # Dataset size in bytes
            doi: Optional[str]         # DOI if available
            url: str                   # URL to dataset
            source: str                # Source repository (e.g., 'openneuro', 'dandi')
            date_created: str          # ISO format date
            authors: List[str]         # Dataset authors
            license: Optional[str]      # Dataset license
            subject_count: Optional[int] # Number of subjects in dataset
            data_standard: Optional[str] # Data standard used (e.g., 'BIDS', 'NWB')
    """
    id: str                     # Unique identifier
    name: str                   # Dataset name
    description: str            # Full description/readme
    modalities: List[str]       # Imaging/recording modalities
    species: List[str]         # Study species
    tasks: List[str]           # Experimental tasks
    size: int                  # Dataset size in bytes
    doi: Optional[str]         # DOI if available
    url: str                   # URL to dataset
    source: str                # Source repository (e.g., 'openneuro', 'dandi')
    date_created: str          # ISO format date
    authors: List[str]         # Dataset authors
    license: Optional[str]      # Dataset license
    subject_count: Optional[int] # Number of subjects in dataset
    data_standard: Optional[str] # Data standard used (e.g., 'BIDS', 'NWB')