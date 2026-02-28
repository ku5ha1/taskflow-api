import logging
import uuid
from typing import Optional
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from app.utils.database import SessionLocal
from app.models.file_metadata import FileMetadata
from app.config import settings

logger = logging.getLogger(__name__)


class StorageConnectionError(Exception):
    """Raised when storage service connection fails"""
    pass


class StorageService:
    """S3-compatible storage abstraction using MinIO"""
    
    def __init__(self, endpoint_url: str = None, access_key: str = None, secret_key: str = None, bucket_name: str = None):
        """Initialize S3 client with MinIO configuration"""
        self.bucket_name = bucket_name or settings.s3_bucket_name
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url or settings.s3_endpoint_url,
            aws_access_key_id=access_key or settings.aws_access_key_id,
            aws_secret_access_key=secret_key or settings.aws_secret_access_key,
            region_name='us-east-1'
        )
    
    def ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    if create_error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                        logger.info(f"Bucket {self.bucket_name} already owned by you")
                    else:
                        raise StorageConnectionError(f"Failed to create bucket: {create_error}")
            else:
                raise StorageConnectionError(f"Failed to check bucket: {e}")
        except EndpointConnectionError as e:
            raise StorageConnectionError(f"Failed to connect to storage service: {e}")

    
    async def upload_file(self, file_content: bytes, filename: str, content_type: str, user_id: int) -> dict:
        """
        Upload file to MinIO and store metadata in PostgreSQL
        Returns: {file_id: str, url: str, metadata: dict}
        """
        try:
            file_id = uuid.uuid4()
            s3_key = f"uploads/{user_id}/{file_id}/{filename}"
            
            # Upload to MinIO
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ACL='private'
            )
            
            # Store metadata in PostgreSQL
            db = SessionLocal()
            try:
                file_metadata = FileMetadata(
                    id=file_id,
                    filename=filename,
                    content_type=content_type,
                    size_bytes=len(file_content),
                    s3_key=s3_key,
                    bucket_name=self.bucket_name,
                    uploaded_by=user_id
                )
                db.add(file_metadata)
                db.commit()
                db.refresh(file_metadata)
                
                # Generate signed URL
                signed_url = self.generate_signed_url(str(file_id))
                
                return {
                    "file_id": str(file_id),
                    "url": signed_url,
                    "metadata": {
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": len(file_content)
                    }
                }
            finally:
                db.close()
                
        except EndpointConnectionError as e:
            raise StorageConnectionError(f"Failed to connect to storage service: {e}")
        except ClientError as e:
            raise StorageConnectionError(f"Failed to upload file: {e}")

    
    def download_file(self, file_id: str) -> bytes:
        """Download file content from MinIO by file_id"""
        try:
            db = SessionLocal()
            try:
                file_metadata = db.query(FileMetadata).filter(
                    FileMetadata.id == file_id,
                    FileMetadata.deleted_at.is_(None)
                ).first()
                
                if not file_metadata:
                    raise FileNotFoundError(f"File {file_id} not found in storage")
                
                response = self.s3_client.get_object(
                    Bucket=file_metadata.bucket_name,
                    Key=file_metadata.s3_key
                )
                return response['Body'].read()
            finally:
                db.close()
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File {file_id} not found in storage")
            raise StorageConnectionError(f"Failed to download file: {e}")
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file from MinIO and soft delete metadata in PostgreSQL"""
        try:
            db = SessionLocal()
            try:
                file_metadata = db.query(FileMetadata).filter(
                    FileMetadata.id == file_id,
                    FileMetadata.deleted_at.is_(None)
                ).first()
                
                if not file_metadata:
                    raise FileNotFoundError(f"File {file_id} not found in storage")
                
                # Hard delete from MinIO
                self.s3_client.delete_object(
                    Bucket=file_metadata.bucket_name,
                    Key=file_metadata.s3_key
                )
                
                # Soft delete in PostgreSQL
                from datetime import datetime
                file_metadata.deleted_at = datetime.utcnow()
                db.commit()
                
                return True
            finally:
                db.close()
                
        except ClientError as e:
            raise StorageConnectionError(f"Failed to delete file: {e}")
    
    def generate_signed_url(self, file_id: str, expiration: int = 3600) -> str:
        """Generate time-limited signed URL for file access"""
        try:
            db = SessionLocal()
            try:
                file_metadata = db.query(FileMetadata).filter(
                    FileMetadata.id == file_id,
                    FileMetadata.deleted_at.is_(None)
                ).first()
                
                if not file_metadata:
                    raise FileNotFoundError(f"File {file_id} not found in storage")
                
                signed_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': file_metadata.bucket_name,
                        'Key': file_metadata.s3_key
                    },
                    ExpiresIn=expiration
                )
                return signed_url
            finally:
                db.close()
                
        except ClientError as e:
            raise StorageConnectionError(f"Failed to generate signed URL: {e}")


async def check_storage_health() -> bool:
    """Health check for MinIO storage connectivity"""
    try:
        storage = StorageService()
        storage.s3_client.list_buckets()
        return True
    except Exception:
        return False
