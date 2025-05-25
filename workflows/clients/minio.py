"""Thin client for MinIO object storage."""

import os
import urllib.parse
from datetime import datetime

import boto3
from botocore.client import Config

from workflows.constants import (
    DEFAULT_CONTENT_TYPE,
    MINIO_BUCKET_NAME,
)


class MinioClient:
    """Simple client for MinIO S3-compatible storage."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
        region: str = "us-east-1",
    ):
        """Initialize the MinIO client.

        Args:
            endpoint: The MinIO server endpoint (default from env var MINIO_ENDPOINT)
            access_key: MinIO access key (default from env var MINIO_ACCESS_KEY)
            secret_key: MinIO secret key (default from env var MINIO_SECRET_KEY)
            secure: Whether to use HTTPS (default from env var MINIO_SECURE)
            region: MinIO region (default: us-east-1)
        """
        self.endpoint = endpoint or os.environ.get(
            "MINIO_ENDPOINT", "http://localhost:9000"
        )
        self.access_key = access_key or os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        self.secure = (
            secure
            if secure is not None
            else os.environ.get("MINIO_SECURE", "").lower() == "true"
        )
        self.region = region

        # Set up the S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version="s3v4"),
            verify=self.secure,
        )

        # Store the endpoint for URL generation (strip trailing slash)
        self.endpoint_for_url = self.endpoint.rstrip("/")

    def ensure_bucket_exists(self, bucket_name: str = MINIO_BUCKET_NAME) -> None:
        """Ensure the bucket exists, creating it if necessary.

        Args:
            bucket_name: Name of the bucket to check/create
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except Exception:
            self.s3_client.create_bucket(Bucket=bucket_name)

    def upload_image(
        self,
        image_bytes: bytes,
        filename: str | None = None,
        bucket_name: str = MINIO_BUCKET_NAME,
        content_type: str = DEFAULT_CONTENT_TYPE,
    ) -> str:
        """Upload an image to MinIO.

        Args:
            image_bytes: The image data as bytes
            filename: Optional filename, if not provided a timestamp-based name is generated
            bucket_name: Name of the bucket to upload to
            content_type: Content type of the image

        Returns:
            Public URL for the uploaded image
        """
        # Ensure bucket exists
        self.ensure_bucket_exists(bucket_name)

        # Generate a unique key if filename not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            filename = f"img_{timestamp}.png"

        # Upload the image
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=image_bytes,
            ContentType=content_type,
        )

        # Generate and return the public URL
        # Use urllib to properly construct and encode the URL
        base_url = urllib.parse.urlparse(self.endpoint_for_url)
        path = f"/{bucket_name}/{filename}"

        # Create a new URL with the bucket and object path
        url_parts = (base_url.scheme, base_url.netloc, path, "", "", "")
        url = urllib.parse.urlunparse(url_parts)

        return url
