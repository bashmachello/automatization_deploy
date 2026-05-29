import random
import uuid
from datetime import datetime
import numpy as np
import pandas as pd
from config import (
    MAX_CASH_PER_SHOP,
    MAX_RECEIPTS_PER_CASH,
    MAX_SHOPS,
    PAYMENT_TYPE,
    PRODUCTS
)
from utils.logger import get_logger
from utils.tg_handler import send_to_tg

logger = get_logger(__name__)


def generate_shops():
    rows = []
    shop_count = random.randint(1, MAX_SHOPS)
    shop_ids = random.sample(range(1, MAX_SHOPS + 1), shop_count)
    for shop_id in shop_ids:
        rows.append({
            'shop_id': shop_id,
            'shop_name': f'Shop_{shop_id}',
        })
    return pd.DataFrame(rows)


def generate_cashes(shops_df):
    rows = []
    for shop_id in shops_df.shop_id:
        cash_count = random.randint(1, MAX_CASH_PER_SHOP)
        cash_ids = random.sample(range(1, MAX_CASH_PER_SHOP + 1), cash_count)
        for cash_id in cash_ids:
            rows.append({
                'shop_id': shop_id,
                'cash_id': cash_id,
            })
    return pd.DataFrame(rows)


def generate_item(doc_id):
    category = random.choice(list(PRODUCTS.keys()))
    item = random.choice(PRODUCTS[category])
    amount = random.randint(1, 10)
    price = round(np.random.uniform(1, 10000), 2)
    discount = np.random.randint(0, 75)
    total = round(amount * price * (1 - discount / 100), 2)
    return {
        'doc_id': doc_id,
        'category': category,
        'item': item,
        'amount': amount,
        'price': price,
        'discount': discount,
        'total': total,
    }


def generate_receipt(shop_id, cash_id):
    doc_id = uuid.uuid4().hex
    receipt = {
        'doc_id': doc_id,
        'shop_id': shop_id,
        'cash_id': cash_id,
        'receipt_date': datetime.now(),
        'payment_type': random.choice(PAYMENT_TYPE)
    }
    items = []
    num_items = np.random.randint(1, 15)
    for _ in range(num_items):
        items.append(generate_item(doc_id))
    return receipt, items


def generate_daily_data():
    if datetime.today().weekday() == 6:
        logger.info(f'Skip Sunday')
        return None, None, None, None
    shops_df = generate_shops()
    cashes_df = generate_cashes(shops_df)
    all_receipts = []
    all_receipt_items = []
    for _, cash_row in cashes_df.iterrows():
        shop_id = cash_row['shop_id']
        cash_id = cash_row['cash_id']
        num_receipts_for_cash = random.randint(1, MAX_RECEIPTS_PER_CASH)
        for _ in range(num_receipts_for_cash):
            receipt, items = generate_receipt(shop_id, cash_id)
            all_receipts.append(receipt)
            all_receipt_items.extend(items)
    return pd.DataFrame(all_receipts), pd.DataFrame(all_receipt_items), shops_df, cashes_df


def generate_data():
    receipts_df, items_df, shops_df, cashes_df = generate_daily_data()
    return receipts_df, items_df, shops_df, cashes_df


def export_to_minio(receipts_df, items_df, minio):
    merged = receipts_df.merge(items_df, on='doc_id')
    uploaded_count = 0
    total_rows = 0
    logger.info(f'Merged {len(merged)} rows')
    for (shop_id, cash_id), group in merged.groupby(['shop_id', 'cash_id']):
        filename = f'{shop_id}_{cash_id}.csv'
        export_data = group[['doc_id', 'item', 'category', 'amount', 'price', 'discount']]
        minio.upload_df(export_data, filename)
        uploaded_count += 1
        total_rows += len(export_data)
        logger.info(f'Загружено {len(export_data)} записей в {filename}')
    send_to_tg(f"Загружено {uploaded_count} файлов ({total_rows} строк) в MinIO")
