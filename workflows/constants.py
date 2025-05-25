"""Prefect-related constants."""

# Task retry settings
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# Prefect Client Constants
BACKGROUND_REMOVAL_FLOW = "background-removal"
BACKGROUND_REMOVAL_DEPLOYMENT = "background-removal-deployment"
DEFAULT_WORKER_POOL = "test-pool"
FLOW_DOCKERFILE = "workflows/Dockerfile.flows"

# MinIO Constants
MINIO_BUCKET_NAME = "processed-images"
MINIO_PUBLIC_URL_FORMAT = "{endpoint}/{bucket}/{key}"
DEFAULT_IMAGE_FORMAT = "png"
DEFAULT_CONTENT_TYPE = "image/png"
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"  # noqa: S105

# Other / Misc
DEFAULT_REQUEST_TIMEOUT = 10.0
