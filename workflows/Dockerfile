FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the workflows code
COPY . /app/workflows/

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Run the deployment script
CMD ["python", "workflows/flows/deploy.py"]
