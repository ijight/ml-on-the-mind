# Use Python base image
FROM python:3.9-slim

# Install PDM
RUN pip install pdm

# Set working directory
WORKDIR /app

# Set PDM environment variables
ENV PDM_USE_VENV=false
ENV PDM_IGNORE_SAVED_PYTHON=1

# Copy project files
COPY . .

# Install dependencies
RUN pdm install --no-self

# NOTE: Only necessary if you want to do the initial dataset download and vector DB build
# On the remote server, otherwise just run locally on the remote server (will be faster).

# # Download datasets and build vector DB
# RUN pdm run python -m src.ml_on_the_mind.download.openneuro_downloader && \
#     pdm run python -m src.ml_on_the_mind.download.dandi_downloader

# RUN pdm run python -m src.ml_on_the_mind.build_vector_db

# Start Streamlit
CMD ["pdm", "run", "streamlit", "run", "src/ml_on_the_mind/app.py"] 