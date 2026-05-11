"""S3-compatible blob storage adapter."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.client import Config

from app.config import get_settings


class BlobStorage:
    def __init__(self) -> None:
        s = get_settings()
        self._bucket = s.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=s.s3_endpoint_url,
            aws_access_key_id=s.s3_access_key,
            aws_secret_access_key=s.s3_secret_key,
            region_name=s.s3_region,
            config=Config(signature_version="s3v4"),
        )

    def put(self, key: str, body: bytes | BinaryIO, content_type: str = "application/octet-stream") -> str:
        data = body if isinstance(body, (bytes, bytearray)) else body.read()
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"].read()

    def presigned_get(self, key: str, expires: int = 900) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )


_storage: BlobStorage | None = None


def get_storage() -> BlobStorage:
    global _storage
    if _storage is None:
        _storage = BlobStorage()
    return _storage
