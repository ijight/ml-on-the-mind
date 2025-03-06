# Use Python base image
FROM python:3.9-slim

# Install PDM
RUN pip install pdm

# Install dependencies
RUN pdm install --no-self

# Download datasets and build vector DB
RUN pdm run python -m src.ml_on_the_mind.download.openneuro_downloader && \
    pdm run python -m src.ml_on_the_mind.download.dandi_downloader && \
    pdm run python -m src.ml_on_the_mind.build_vector_db

# Expose Streamlit port
EXPOSE 8501

# Start Streamlit
CMD ["pdm", "run", "streamlit", "run", "src/ml_on_the_mind/app.py"] 