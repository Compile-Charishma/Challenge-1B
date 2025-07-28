# Use official Python image
FROM python:3.11-slim

# Install system dependencies for fitz (PyMuPDF) and build tools
RUN apt-get update && \
    apt-get install -y gcc libmupdf-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Set the entrypoint
CMD ["python", "persona_main.py"]