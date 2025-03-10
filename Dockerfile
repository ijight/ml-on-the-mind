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

# Download datasets and build vector DB
RUN pdm run python -m src.ml_on_the_mind.download.openneuro_downloader && \
    pdm run python -m src.ml_on_the_mind.download.dandi_downloader

# Add Docker's official GPG key:
RUN apt-get update
RUN apt-get install ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc
    
# Add the repository to Apt sources:
RUN echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
       tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update

RUN apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

RUN docker run hello-world

# Start Marqo
RUN docker pull marqoai/marqo:latest
RUN docker run --name marqo -d -p 8882:8882 marqoai/marqo:latest

RUN pdm run python -m src.ml_on_the_mind.build_vector_db

# Start Streamlit
CMD ["streamlit", "run", "src/ml_on_the_mind/app.py"] 