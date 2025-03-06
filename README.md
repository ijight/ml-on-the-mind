# Neuroscience Dataset Search

Large scale neural data is becoming increasingly available, but it can be difficult to find the right dataset for a given question. This project is a semantic search interface for exploring neuroscience datasets from OpenNeuro, DANDI, and BIDS using natural language queries.

## Usage

1. Enter search terms in the search bar to find relevant datasets
2. Use the sidebar filters to narrow down results by:
   - Imaging modality
   - Species
   - Task type
   - Dataset size
3. Click dataset titles to view them on their respective websites
4. Expand README sections to learn more about each dataset

## Dependencies

- marqo-python
- streamlit
- Docker (for running Marqo)

## Initial Setup
This project uses PDM to manage dependencies. To install the dependencies, run:

```
pdm install
```

To run the dataset downloaders, run:

```
python -m src.ml_on_the_mind.download.openneuro_downloader
python -m src.ml_on_the_mind.download.dandi_downloader
```

To run the database, run:

```
docker rm -f marqo
docker pull marqoai/marqo:latest
docker run --name marqo -it -p 8882:8882 marqoai/marqo:latest
```

To load the data into the database, run:

```
python -m src.ml_on_the_mind.build_vector_db
```

To run the app, run:

```
streamlit run src/ml_on_the_mind/app.py
```


