import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class PGDatabase:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.database = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )
        logger.info('Connected to PostgreSQL')
        self.cur = self.conn.cursor()
        self.conn.autocommit = False

    def __enter__(self):
        logger.info('Postgres connect is inizialized')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info('Postgres connect is closed')
        self.close()

    def insert_shop(self, shops_df):
        data = list(
            shops_df[['shop_id', 'shop_name']]
            .itertuples(index=False, name=None)
        )
        execute_values(self.cur,
                       """
                       INSERT INTO shops (shop_id, shop_name)
                       VALUES %s ON CONFLICT (shop_id) DO NOTHING""",
                       data)
        logger.info(f'Inserted {len(data)} shops')

    def insert_cashes(self, cashes_df):
        data = list(
            cashes_df[['cash_id', 'shop_id']]
            .itertuples(index=False, name=None)
        )
        execute_values(self.cur,
                       """
                       INSERT INTO cashes (cash_id, shop_id)
                       VALUES %s ON CONFLICT (shop_id, cash_id) DO NOTHING""",
                       data)
        logger.info(f'Inserted {len(data)} cashes')

    def insert_receipts(self, receipt_df):
        data = list(
            receipt_df[['doc_id', 'shop_id', 'cash_id', 'receipt_date', 'payment_type']]
            .itertuples(index=False, name=None)
        )
        execute_values(self.cur,
                       """
                       INSERT INTO receipts (doc_id, shop_id, cash_id, receipt_date, payment_type)
                       VALUES %s ON CONFLICT (doc_id) DO NOTHING""",
                       data)
        logger.info(f'Inserted {len(data)} receipts')

    def insert_receipt_items(self, receipt_items_df):
        data = list(
            receipt_items_df[['doc_id', 'category', 'item', 'amount', 'price', 'discount', 'total']]
            .itertuples(index=False, name=None)
        )
        execute_values(self.cur,
                       """
                       INSERT INTO receipts_items (doc_id, category, item, amount, price, discount, total)
                       VALUES %s""",
                       data)
        logger.info(f'Inserted {len(data)} receipt items')

    def post(self, query, args=None):
        try:
            self.cur.execute(query, args)
            logger.info(f'Insert успешен, строк затронуто: {self.cur.rowcount}')
        except Exception:
            logger.exception('Insert failed')

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info('Postgres closed')
