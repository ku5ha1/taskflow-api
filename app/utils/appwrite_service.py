import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.input_file import InputFile
from appwrite.exception import AppwriteException

load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_SECRET = os.getenv("APPWRITE_SECRET")
APPWRITE_BUCKET_ID = os.getenv("APPWRITE_BUCKET_ID")

if not all([APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_SECRET, APPWRITE_BUCKET_ID]):
    raise ValueError("Missing Appwrite configuration. Ensure endpoint, project, secret, and bucket are set.")

client = (
    Client()
    .set_endpoint(APPWRITE_ENDPOINT)
    .set_project(APPWRITE_PROJECT_ID)
    .set_key(APPWRITE_SECRET)
    .set_self_signed()
)

storage = Storage(client)

def upload_bytes_to_bucket(filename: str, content: bytes, permissions=None) -> dict:
    if permissions is None:
        permissions = ['read("any")']

    file_input = InputFile.from_bytes(bytes=content, filename=filename)
    try:
        uploaded = storage.create_file(
            bucket_id=APPWRITE_BUCKET_ID,
            file_id=ID.unique(),
            file=file_input,
            permissions=permissions,
        )
        file_id = uploaded["$id"]
        return {
            "id": file_id,
            "filename": filename,
            "url": f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{file_id}/view",
            "raw": uploaded,
        }
    except AppwriteException as e:
        raise RuntimeError(f"Appwrite upload failed: {e.message}") from e