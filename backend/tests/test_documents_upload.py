from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_document_pushes_to_minio():
    class FakeMinioClient:
        def __init__(self, *args, **kwargs):
            self.uploaded = []

        def put_object(self, bucket_name, object_name, data, length, content_type):
            self.uploaded.append(("put_object", bucket_name, object_name, length, content_type))

    with patch("app.documents.api._get_minio_client", return_value=FakeMinioClient()):
        response = client.post(
            "/documents/upload",
            files={"file": ("sample.txt", b"hello world", "text/plain")},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "sample.txt"
    assert body["bucket"] == "documents"
    assert body["size"] == 11
    assert body["object_name"].endswith(".txt")


def test_get_document_returns_uploaded_content():
    class FakeResponse:
        def __init__(self, payload: bytes):
            self.payload = payload

        def read(self) -> bytes:
            return self.payload

        def close(self) -> None:
            return None

    class FakeMinioClient:
        def __init__(self, *args, **kwargs):
            self.downloaded = []

        def get_object(self, bucket_name, object_name):
            self.downloaded.append((bucket_name, object_name))
            return FakeResponse(b"hello from minio")

    with patch("app.documents.api._get_minio_client", return_value=FakeMinioClient()):
        response = client.get("/documents/sample-object.txt")

    assert response.status_code == 200
    assert response.content == b"hello from minio"
    assert response.headers["content-type"].startswith("text/plain")
