import re
from datetime import datetime
import pandas as pd
from psycopg2.extras import execute_values
from storage.minio_client import MinIOClient
from storage.pgdb import PGDatabase
from utils.logger import get_logger
from utils.tg_handler import send_to_tg, safe_send

logger = get_logger(__name__)

def read_from_minio(minio):
    pattern = re.compile(r'^(\d+)_(\d+)\.csv$')
    files = minio.list_files(prefix='data/')

    result = []

    for file_key in files:
        filename = file_key.split('/')[-1]
        if not pattern.match(filename):
            logger.info(f'File {file_key} does not match pattern {pattern}')
            continue
        logger.info(f'Reading file {file_key}')

        response = minio.client.get_object(Bucket=minio.bucket, Key=file_key)
        df = pd.read_csv(response['Body'])
        response['Body'].close()

        #filename = file_key.split('/')[-1]
        shop_id, cash_id = map(int, filename.replace('.csv', '').split('_'))
        result.append({
            'df': df,
            'shop_id': shop_id,
            'cash_id': cash_id,
            'filename': filename,
            'file_key': file_key
        })
    return result


def from_minio_to_db(minio):
    with PGDatabase() as db:
        total_loaded = 0
        all_files_data = read_from_minio(minio)
        if not all_files_data:
            logger.info('Nothing to load')
            return

        today = datetime.now().strftime('%Y-%m-%d')
        processed_prefix = f'processed/{today}/'
        for file_data in all_files_data:
            df = file_data['df']
            filename = file_data['filename']
            file_key = file_data['file_key']

            processed_key = f'{processed_prefix}{filename}'

            data = list(
                df[['doc_id', 'item', 'category', 'amount', 'price', 'discount']]
                .itertuples(index=False, name=None)
            )

            try:
                execute_values(db.cur,
                               """
                               INSERT INTO sales (doc_id, item, category, amount, price, discount)
                               VALUES %s ON CONFLICT
                               ON CONSTRAINT sales_unique DO NOTHING""",
                               data)
                db.conn.commit()

                copy_source = {'Bucket': minio.bucket, 'Key': file_key}
                minio.client.copy_object(CopySource=copy_source, Bucket=minio.bucket, Key=processed_key)
                minio.client.delete_object(Bucket=minio.bucket, Key=file_key)
                logger.info(f'{filename} loaded and deleted')
                total_loaded += len(data)
                logger.info(f'Saved {len(data)} rows from {filename} to Sales')
            except Exception:
                db.conn.rollback()
                logger.exception(f'Failed processing {filename}')
                safe_send(f'Failed loading {filename}')
        logger.info(f'Total rows saved: {total_loaded}')
        safe_send(f'Total rows saved {total_loaded} to DB')


if __name__ == "__main__":
    from_minio_to_db( MinIOClient())
