import os
from time import sleep

from minio import Minio


def main() -> None:
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
    bucket_name = os.getenv("MINIO_BUCKET", "documents")

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    for _ in range(20):
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            break
        except Exception:
            sleep(2)
    else:
        raise RuntimeError(f"Unable to initialize MinIO bucket: {bucket_name}")


if __name__ == "__main__":
    main()
