import os.path
from typing import Optional, List

from boto3 import Session
from botocore.exceptions import ClientError

from settings import settings
from domain.file import FileRepository, Content


class FileRepositoryS3(FileRepository):

    def __init__(self) -> None:
        self._session = Session(region_name=settings.AWS_S3_REGION,
                                aws_access_key_id=settings.AWS_S3_ACCESS_KEY,
                                aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY)

        s3_resource = self._session.resource('s3')
        self._client = self._session.client('s3')

        bucket = s3_resource.Bucket(settings.AWS_S3_BUCKET_NAME)
        self._bucket = bucket

    def upload(self, file_path: str, object_key: str):
        with open(file_path, 'rb') as f:
            try:
                self._bucket.upload_fileobj(f, object_key)
            except Exception:
                raise

    def exists(self, object_key: str) -> bool:
        try:
            bucket = settings.AWS_S3_BUCKET_NAME
            self._client.head_object(Bucket=bucket, Key=object_key)
            return True
        except ClientError:
            return False
        except Exception:
            raise

    def download(self, object_key: str, save_path: str):
        try:
            self._bucket.download_file(object_key, save_path)
        except Exception:
            raise

    def delete(self, object_key: str):
        try:
            bucket = settings.AWS_S3_BUCKET_NAME
            self._client.delete_object(Bucket=bucket, Key=object_key)
        except Exception:
            raise

    def get_contents(self, object_key_prefix: str) -> List[Content]:
        objs = self._bucket.meta.client.list_objects_v2(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Prefix=object_key_prefix
        )

        contents = objs.get('Contents')
        if not contents:
            return []

        # ファイルのみに絞りこむ
        results = []
        for content in contents:
            object_key: str = content.get('Key')
            name: str = os.path.basename(object_key)
            # name: str = f'{object_key_prefix}/{name}' if object_key_prefix else name
            is_file: bool = not name.endswith('/')
            updated_at = content.get('LastModified')

            results.append(Content(name=name, object_key=object_key, is_file=is_file, updated_at=updated_at))

        return results
