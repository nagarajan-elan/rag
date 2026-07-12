from __future__ import annotations

import io
import mimetypes
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
}

CONTENT_TYPE_TO_EXTENSION = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/csv": ".csv",
    "application/json": ".json",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}


def _get_minio_client() -> Any:
    try:
        from minio import Minio
    except ImportError as exc:  # pragma: no cover - exercised only when dependency is missing
        raise RuntimeError("minio package is required to upload files") from exc

    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    if not access_key or not secret_key:
        raise RuntimeError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY must be configured")

    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def _resolve_extension(filename: str | None, content_type: str | None) -> str:
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in ALLOWED_EXTENSIONS:
            return suffix

    if content_type and content_type in CONTENT_TYPE_TO_EXTENSION:
        return CONTENT_TYPE_TO_EXTENSION[content_type]

    guessed_type, _ = mimetypes.guess_type(filename or "")
    if guessed_type and guessed_type in CONTENT_TYPE_TO_EXTENSION:
        return CONTENT_TYPE_TO_EXTENSION[guessed_type]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Unsupported file type. Allowed extensions: "
            + ", ".join(sorted(ALLOWED_EXTENSIONS))
        ),
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A file name is required")

    extension = _resolve_extension(file.filename, file.content_type)
    bucket_name = os.getenv("MINIO_BUCKET", "documents")
    object_name = f"{uuid4().hex}{extension}"
    content = await file.read()

    try:
        client = _get_minio_client()
        client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(content),
            length=len(content),
            content_type=file.content_type or "application/octet-stream",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - depends on MinIO availability
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {exc}") from exc
    finally:
        await file.close()

    return {
        "filename": file.filename,
        "object_name": object_name,
        "bucket": bucket_name,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
    }
