# Use Python base image
FROM python:3.9-slim

# Install PDM
RUN pip install pdm

# Set working directory
WORKDIR /app

# Set PDM environment variables
ENV PDM_USE_VENV=false
ENV PDM_IGNORE_SAVED_PYTHON=1

# Install dependencies
RUN ls -la
RUN pdm init
RUN pdm install --no-self -v

# Download datasets and build vector DB
RUN pdm run python -m src.ml_on_the_mind.download.openneuro_downloader && \
    pdm run python -m src.ml_on_the_mind.download.dandi_downloader && \
    pdm run python -m src.ml_on_the_mind.build_vector_db

# Expose Streamlit port
EXPOSE 8501

# Start Streamlit
CMD ["pdm", "run", "streamlit", "run", "src/ml_on_the_mind/app.py"] 