# Background Remover Service

A high-performance FastAPI service that removes backgrounds from images using the Photoroom API. This service supports both single image processing and batch processing with parallel execution.

## 🌟 Features

- **Single Image Processing**: Remove background from individual images via URL
- **Batch Processing**: Process multiple images in parallel with consolidated results
- **High Performance**: Async/await architecture with parallel API calls
- **Production Ready**: Built with FastAPI, comprehensive error handling, and API documentation
- **Easy Setup**: Uses `uv` for fast dependency management

## 🏗️ Project Structure

```
background-remover/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── clients/
│   │   └── photoroom.py     # Photoroom API client
│   ├── models/
│   │   └── __init__.py      # Pydantic request/response models
│   └── routers/
│       └── background_remover.py  # API endpoints
├── tests/                   # Test directory (pytest ready)
├── pyproject.toml          # Project configuration
└── README.md
```

## 🚀 Setup

### Prerequisites
- Python 3.8+
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
   uv pip install -e .
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set your Photoroom API key:
   # PHOTOROOM_API_KEY=your_actual_api_key_here
   ```

4. **Start the service:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The service will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 📡 API Endpoints

### Health Check
- **GET** `/` - Service status
- **GET** `/health` - Health check

### Background Removal (Standard)
- **POST** `/api/v1/remove-background` - Remove background from single image
- **POST** `/api/v1/remove-backgrounds` - Batch process multiple images

### Experimental: Prefect-based Parallel Processing
**⚠️ Note: This is experimental and incomplete due to time constraints**

- **POST** `/api/v1/prefect/remove-backgrounds-async` - Start async batch processing with Prefect
- **GET** `/api/v1/prefect/status/{flow_id}` - Check processing status 
- **GET** `/api/v1/prefect/download/{flow_id}` - Download completed results

This experimental implementation uses [Prefect 3.x](https://www.prefect.io/) for workflow orchestration and parallel task execution. The idea was to:

1. **True Parallelism**: Use Prefect workers to distribute image processing tasks across multiple workers
2. **Durable Execution**: Leverage Prefect's built-in retry logic, error handling, and state persistence
3. **Monitoring**: Provide real-time status tracking and progress monitoring through Prefect UI
4. **Scalability**: Enable horizontal scaling by adding more Prefect workers

**Current Implementation Status:**
- ✅ Basic Prefect flow structure in `workflows/flows/background_remover.py`
- ✅ Prefect deployment configuration in `workflows/flows/deploy.py`
- ✅ FastAPI router with async endpoints in `app/routers/background_remover_parallel.py`
- ✅ Docker Compose setup with Prefect server
- ❌ **Incomplete**: Full integration and testing ran out of time

**To explore this experimental feature:**
```bash
# Start services with Prefect
docker-compose up -d

# Access Prefect UI at http://localhost:4200
# API endpoints available at /api/v1/prefect/*
```

See `workflows/README.md` for more details on the intended architecture.

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

### Python Client Example
```python
import httpx
import asyncio

async def remove_background(image_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/remove-background",
            json={"image_url": image_url}
        )
        if response.status_code == 200:
            with open("result.png", "wb") as f:
                f.write(response.content)
            return "Success!"
        return f"Error: {response.text}"

# Usage
result = asyncio.run(remove_background("https://example.com/image.jpg"))
print(result)
```

## 🏗️ Development

### Development Dependencies
This project uses several development tools to maintain code quality:
- **[Invoke](https://www.pyinvoke.org/)** - Task execution tool for automation
- **[Ruff](https://docs.astral.sh/ruff/)** - An extremely fast Python linter and code formatter
- **[Pytest](https://docs.pytest.org/)** - Testing framework

Install all development dependencies:
```bash
uv pip install -e ".[dev]"
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
```

### Manual Tool Usage

If you prefer to run tools manually:

```bash
# Linting and formatting with ruff
ruff check .
ruff format .

# Running tests with pytest
pytest
pytest --cov=app  # With coverage
```
