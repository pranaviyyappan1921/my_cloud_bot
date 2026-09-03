import os

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

AZURE_STORAGE_CONTAINER = os.getenv(
    "AZURE_STORAGE_CONTAINER",
    "uploaded-files"
)


def get_blob_service_client():
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING is not configured."
        )

    return BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )


def get_container_client():
    client = get_blob_service_client()

    return client.get_container_client(
        AZURE_STORAGE_CONTAINER
    )


def upload_file(file_data, blob_name, content_type=None):
    container_client = get_container_client()

    blob_client = container_client.get_blob_client(
        blob_name
    )

    content_settings = None

    if content_type:
        content_settings = ContentSettings(
            content_type=content_type
        )

    blob_client.upload_blob(
        file_data,
        overwrite=True,
        content_settings=content_settings
    )

    return blob_name


def download_file(blob_name):
    container_client = get_container_client()

    blob_client = container_client.get_blob_client(
        blob_name
    )

    return blob_client.download_blob().readall()


def delete_file(blob_name):
    container_client = get_container_client()

    blob_client = container_client.get_blob_client(
        blob_name
    )

    blob_client.delete_blob()

    return True


def blob_exists(blob_name):
    container_client = get_container_client()

    blob_client = container_client.get_blob_client(
        blob_name
    )

    return blob_client.exists()


def list_files():
    container_client = get_container_client()

    return [
        blob.name
        for blob in container_client.list_blobs()
    ]


def check_connection():
    try:
        container_client = get_container_client()

        container_client.get_container_properties()

        return True

    except Exception as e:
        print(
            f"Azure Blob Storage connection error: {e}"
        )

        return False