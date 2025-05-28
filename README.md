<!-- filepath: [REDACTED] -->
# [REDACTED] Service

A high-performance FastAPI service that removes backgrounds from images using the [REDACTED] API. This service supports both single image processing and batch processing with parallel execution.

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
[REDACTED]/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── clients/
│   │   └── [REDACTED].py    # [REDACTED] API client
│   ├── models/
│   │   └── [REDACTED].py    # Pydantic request/response models
│   └── routers/
│       ├── [REDACTED].py    # Standard API endpoints
│       └── [REDACTED]_parallel.py  # Prefect-based API endpoints
├── workflows/
│   ├── clients/
│   │   ├── [REDACTED].py    # Thin [REDACTED] client
│   │   └── minio.py         # Thin MinIO client
│   └── flows/
│       └── [REDACTED].py    # Prefect workflow definition
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
   cd [REDACTED]
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
   # Edit .env and set your [REDACTED] API key:
   # [REDACTED]_API_KEY=your_actual_api_key_here
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

### [REDACTED] (Standard)
- **POST** `/api/v1/remove-background` - Remove background from single image
- **POST** `/api/v1/remove-backgrounds` - Batch process multiple images

### [REDACTED] (Enhanced)

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
   - Through the API: Use the FastAPI endpoints at `/api/v2/*`

4. **Viewing results:**
   - Flow results are stored in MinIO and can be accessed via the URLs returned by the API (you might need to replace the dockerised address, "minio:9000" with "localhost:9001" to view the images).
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

### Truly Parallel Batch Processing with Prefect
```bash
curl -X POST "http://localhost:8000/api/v2/remove-backgrounds" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

The above curl will return the flow_ids to use to query for results. Example:

```json
{
  "flow_ids": [
    "bb756110-a37c-457b-9acd-f6fc16081868",
    "e8d64f58-69db-404c-8541-32c7c2110126",
    "fef9c3ac-033b-4f5e-9a22-3c579cf3e8f9"
  ],
  "message": "Started processing 3 images",
  "status": "RUNNING",
  "image_count": 3
}
```

Then use the `/results` endpoint to get the actual results.

```bash
curl -X POST "http://localhost:8000/api/v2/remove-backgrounds/results" \
  -H "Content-Type: application/json" \
  -d '{
    [
      "flow_id_0",
      "flow_id_1"
    ]
  }'
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
