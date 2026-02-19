import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles

from app.shared.config import get_settings


class StorageService(ABC):
    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """Save file and return the URL/path to access it."""
        pass

    @abstractmethod
    async def delete(self, filename: str) -> bool:
        """Delete file and return success status."""
        pass

    @abstractmethod
    async def get_url(self, filename: str) -> str:
        """Get the URL to access the file."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        file_path = self.upload_dir / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return f"/uploads/{filename}"

    async def delete(self, filename: str) -> bool:
        file_path = self.upload_dir / filename
        if file_path.exists():
            os.remove(file_path)
            return True
        return False

    async def get_url(self, filename: str) -> str:
        return f"/uploads/{filename}"

    def get_absolute_path(self, filename: str) -> Path:
        return self.upload_dir / filename


class S3StorageService(StorageService):
    """AWS S3 storage implementation - extend as needed."""

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        # Initialize boto3 client here when implementing
        # import boto3
        # self.client = boto3.client('s3', ...)

    async def save(self, filename: str, content: bytes) -> str:
        # Implement S3 upload
        # self.client.put_object(Bucket=self.bucket_name, Key=filename, Body=content)
        raise NotImplementedError("S3 storage not yet implemented")

    async def delete(self, filename: str) -> bool:
        # Implement S3 delete
        raise NotImplementedError("S3 storage not yet implemented")

    async def get_url(self, filename: str) -> str:
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"


class SupabaseStorageService(StorageService):
    """Supabase storage implementation - extend as needed."""

    def __init__(self, url: str, key: str, bucket: str):
        self.url = url
        self.key = key
        self.bucket = bucket
        # Initialize supabase client here when implementing
        # from supabase import create_client
        # self.client = create_client(url, key)

    async def save(self, filename: str, content: bytes) -> str:
        # Implement Supabase upload
        raise NotImplementedError("Supabase storage not yet implemented")

    async def delete(self, filename: str) -> bool:
        # Implement Supabase delete
        raise NotImplementedError("Supabase storage not yet implemented")

    async def get_url(self, filename: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{filename}"


def get_storage_service() -> StorageService:
    settings = get_settings()

    if settings.storage_type == "s3":
        if not all(
            [
                settings.aws_access_key_id,
                settings.aws_secret_access_key,
                settings.aws_bucket_name,
            ]
        ):
            raise ValueError("AWS S3 credentials not configured")
        return S3StorageService(
            bucket_name=settings.aws_bucket_name,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            region=settings.aws_region,
        )
    elif settings.storage_type == "supabase":
        if not all(
            [settings.supabase_url, settings.supabase_key, settings.supabase_bucket]
        ):
            raise ValueError("Supabase credentials not configured")
        return SupabaseStorageService(
            url=settings.supabase_url,
            key=settings.supabase_key,
            bucket=settings.supabase_bucket,
        )
    else:
        return LocalStorageService(upload_dir=settings.upload_dir)
