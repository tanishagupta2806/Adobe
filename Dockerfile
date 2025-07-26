# Dockerfile
# Use a base image compatible with linux/amd64 and Python 3.9
# alpine images are smaller, but debian-based are often easier for dependencies
FROM --platform=linux/amd64 python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies first to leverage Docker's cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your application code into the container
COPY . /app/

# --- BONUS FEATURE SETUP: If using Sentence-Transformers (for Round 1B) ---
# You need to manually download the model (e.g., paraphrase-multilingual-MiniLM-L12-v2)
# from Hugging Face or sentence-transformers website.
# Create a 'models' directory in your project root and place the downloaded model files inside it.
# Then uncomment and adjust the following line:
# COPY models/paraphrase-multilingual-MiniLM-L12-v2 /app/models/paraphrase-multilingual-MiniLM-L12-v2

# Command to run your main script when the container starts
# This script will automatically handle input/output directories and choose the round.
CMD ["python", "main.py"]