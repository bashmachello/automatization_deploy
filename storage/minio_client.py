import io
import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt
from utils.logger import get_logger
from utils.tg_handler import send_to_tg, safe_send

load_dotenv()

logger = get_logger(__name__)


class MinIOClient:
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT')
        self.access_key = os.getenv('MINIO_ACCESS_KEY')
        self.secret_key = os.getenv('MINIO_SECRET_KEY')
        self.bucket = os.getenv('MINIO_BUCKET')

        self.client = boto3.client('s3',
                                   endpoint_url=self.endpoint,
                                   aws_access_key_id=self.access_key,
                                   aws_secret_access_key=self.secret_key,
                                   config=Config(signature_version='s3v4'))
        self.ensure_bucket()

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f'Bucket {self.bucket} уже существует')
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)
            logger.info(f'Bucket {self.bucket} создан')

    @retry(stop=stop_after_attempt(3))
    def upload_df(self, df, filename):
        if df.empty:
            return False

        full_path = f'data/{filename}'

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        try:
            self.client.put_object(Bucket=self.bucket, Key=full_path,
                                   Body=csv_buffer.getvalue().encode('utf-8'),
                                   ContentType='text/csv')
            logger.info(f'Uploaded {filename} to {full_path}')
            return True
        except Exception:
            logger.exception(f'Failed to upload {filename} to {full_path}')
            safe_send(f'Failed to upload {filename} to {full_path}')
            raise

    def list_files(self, prefix=''):
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception:
            logger.exception(f'Failed to list files from {prefix}')
            return []
