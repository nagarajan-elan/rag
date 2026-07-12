from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_document_pushes_to_minio():
    class FakeMinioClient:
        def __init__(self, *args, **kwargs):
            self.uploaded = []

        def make_bucket(self, bucket_name):
            self.uploaded.append(("make_bucket", bucket_name))

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
