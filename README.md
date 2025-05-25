# Background Remover Service

A high-performance FastAPI service that removes backgrounds from images using the Photoroom API. This service supports both single image processing and batch processing with parallel execution.

## 🌟 Features

- **Single Image Processing**: Remove background from individual images via URL
- **Batch Processing**: Process multiple images in parallel with consolidated results
- **High Performance**: Async/await architecture with parallel API calls
- **S3 Storage Integration**: Processed images are stored in MinIO (S3-compatible storage)
- **Production Ready**: Built with FastAPI, comprehensive error handling, and API documentation
- **Workflow Orchestration**: Uses Prefect for reliable, scalable task execution
- **Easy Setup**: Uses `uv` for fast dependency management

## 🏗️ Project Structure

```
background-remover/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── clients/
│   │   └── photoroom.py     # Photoroom API client
│   ├── models/
│   │   └── background_remover.py # Pydantic request/response models
│   └── routers/
│       ├── background_remover.py  # Standard API endpoints
│       └── background_remover_parallel.py  # Prefect-based API endpoints
├── workflows/
│   ├── clients/
│   │   ├── photoroom.py     # Thin Photoroom client
│   │   └── minio.py         # Thin MinIO client
│   └── flows/
│       └── background_remover.py  # Prefect workflow definition
├── tests/                   # Test directory (pytest ready)
├── docker-compose.yaml      # Docker services including Prefect and MinIO
├── pyproject.toml           # Project configuration
└── README.md
```

## 🚀 Setup

### Prerequisites
- Python 3.12+
- `uv` package manager ([install here](https://github.com/astral-sh/uv))

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd background-remover
   ```

2. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set your Photoroom API key:
   # PHOTOROOM_API_KEY=your_actual_api_key_here
   ```

4. **Start the service with Docker Compose:**
   ```bash
   uv export > app/requirements.txt
   uv export > workflows/requirements.txt
   docker compose up -d --build
   ```

This will start:
- The FastAPI application on port 8000
- The Prefect server UI on port 4200
- MinIO server on port 9000 with its console on port 9001
- A prefect worker to execute flows

The service will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.
The MinIO console will be available at `http://localhost:9001` (login with minioadmin/minioadmin).

## 📡 API Endpoints

### Health Check
- **GET** `/` - Service status
- **GET** `/health` - Health check

### Background Removal (Standard)
- **POST** `/api/v1/remove-background` - Remove background from single image
- **POST** `/api/v1/remove-backgrounds` - Batch process multiple images

### Experimental: Prefect-based Parallel Processing with S3 Storage

- **POST** `/api/v2/remove-backgrounds` - Start async batch processing with Prefect
- **POST** `/api/v2/remove-backgrounds/results` - Get processing results, including partial results

This implementation uses [Prefect 3.x](https://www.prefect.io/) for workflow orchestration and parallel task execution, 
and MinIO as an S3-compatible storage solution. The architecture:

1. **True Parallelism**: Uses Prefect workers to distribute image processing tasks across multiple workers
2. **Durable Execution**: Leverages Prefect's built-in retry logic, error handling, and state persistence
3. **S3 Storage**: Processed images are stored in MinIO (S3-compatible storage)
4. **Scalability**: Enables horizontal scaling by adding more Prefect workers

**Key Workflow Components:**
- **Single Flow Design**: Each image is processed by a separate Prefect flow for better isolation
- **MinIO Integration**: Processed images are stored in MinIO with a unique URL for retrieval
- **Stateless API**: The API does not store state, making it easy to scale horizontally
- **Partial Results**: The API returns partial results if some flows are still running

**To use this feature:**

Assuming you have already started all docker images with `docker compose`:

```bash
# Create a deployment for the background remover flow
python -m workflows.flows.deploy deploy --name "test-image"

# Access Prefect UI at http://localhost:4200
# Access MinIO Console at http://localhost:9001 (login: minioadmin/minioadmin)
# API endpoints available at /api/v1/prefect/*
```

## 🔄 Prefect Workflows

The application uses Prefect for workflow orchestration. Here's how to work with the Prefect components:

### Monitoring and Managing Flows

1. **Access the Prefect UI:**
   - Open your browser and navigate to http://localhost:4200
   - Here you can monitor flow runs, view logs, and manage deployments

2. **Understanding the components:**
   - **Prefect Server**: Manages flow orchestration and provides the UI
   - **Worker Pool**: A group of workers that can execute flows
   - **Worker**: Executes flows from the assigned worker pool
   - **Deployment**: A registered flow that can be triggered via API or UI

3. **Triggering flows manually:**
   - Through the Prefect UI: Navigate to Deployments and click "Run"
   - Through the API: Use the FastAPI endpoints at `/api/v1/prefect/*`

4. **Viewing results:**
   - Flow results are stored in MinIO and can be accessed via the URLs returned by the API
   - The Prefect UI provides detailed logs and execution history

## 🔧 Usage Examples

### Single Image Processing
```bash
curl -X POST "http://localhost:8000/api/v1/remove-background" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/your-image.jpg"}' \
  --output processed_image.png
```

### Batch Processing
```bash
curl -X POST "http://localhost:8000/api/v1/remove-backgrounds" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

### Python Client Example for Prefect Workflow

```python
import httpx
import asyncio
import json

async def process_images_with_prefect(image_urls):
    async with httpx.AsyncClient() as client:
        # Start processing
        response = await client.post(
            "http://localhost:8000/api/v1/prefect/process",
            json={"image_urls": image_urls}
        )
        
        if response.status_code != 200:
            return f"Error starting processing: {response.text}"
        
        # Get flow IDs
        data = response.json()
        flow_ids = data["flow_ids"]
        
        print(f"Started processing {len(flow_ids)} images. Checking results in 5 seconds...")
        await asyncio.sleep(5)
        
        # Get results (this might return partial results if processing is still ongoing)
        response = await client.post(
            "http://localhost:8000/api/v1/prefect/results",
            json=flow_ids
        )
        
        if response.status_code != 200:
            return f"Error getting results: {response.text}"
        
        results = response.json()
        
        print(f"Processing status: {results['success_count']}/{results['total_count']} completed")
        
        # If you want to wait for all to complete, you can poll until success_count equals total_count
        return results

# Usage
result = asyncio.run(process_images_with_prefect([
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
]))
print(json.dumps(result, indent=2))
```

## 🏗️ Development

### Development Dependencies
This project uses several development tools to maintain code quality:
- **[Invoke](https://www.pyinvoke.org/)** - Task execution tool for automation
- **[Ruff](https://docs.astral.sh/ruff/)** - An extremely fast Python linter and code formatter
- **[Pytest](https://docs.pytest.org/)** - Testing framework

Install all development dependencies:
```bash
uv sync --all-extras
```

### Using Invoke for Development Tasks

This project uses [Invoke](https://www.pyinvoke.org/) to automate common development tasks. You can see all available tasks by running:

```bash
invoke --list
```

#### Common Development Commands

**Linting and Code Quality:**
```bash
# Run ruff linting and formatting
invoke run-lint

# Run pytests
invoke run-tests

# Generate requirements.txt from uv.lock
invoke gen-all-reqs
```
