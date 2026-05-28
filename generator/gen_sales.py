import random
from random import randint, choice
import pandas as pd
import numpy as np
from config import MAX_SHOPS, MAX_CASH_PER_SHOP, PRODUCTS, MAX_RECEIPTS_PER_CASH, PAYMENT_TYPE
from datetime import datetime
import uuid
from utils.logger import get_logger
from utils.tg_handler import send_to_tg

logger = get_logger(__name__)


def generate_shops():
    rows = []
    shop_count = randint(1, MAX_SHOPS)
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
        cash_count = randint(1, MAX_CASH_PER_SHOP)
        cash_ids = random.sample(range(1, MAX_CASH_PER_SHOP + 1), cash_count)
        for cash_id in cash_ids:
            rows.append({
                'shop_id': shop_id,
                'cash_id': cash_id,
            })
    return pd.DataFrame(rows)


def generate_item(doc_id):
    category = choice(list(PRODUCTS.keys()))
    item = choice(PRODUCTS[category])
    amount = randint(1, 5)
    price = round(np.random.uniform(1, 100), 2)
    discount = np.random.randint(0, 100)
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


def generate_receipt(shop_id, cash_id): #, receipt_date):
    doc_id = str(uuid.uuid4())[:8]
    receipt = {
        'doc_id': doc_id,
        'shop_id': shop_id,
        'cash_id': cash_id,
        'receipt_date': datetime.now(), ############
        #'receipt_date': receipt_date,
        'payment_type': choice(PAYMENT_TYPE)
    }
    rows = []
    num_receipts = np.random.randint(1, 3)
    for _ in range(num_receipts):
        rows.append(generate_item(doc_id))
    return receipt, rows


def generate_daily_data(): #######
    #target_date = test_date if test_date else datetime.now()
    if datetime.today().weekday() == 6:
    #if target_date.weekday() == 6:
        #logger.info(f'Skip {target_date.strftime("%A")}')
        logger.info(f'Skip Sunday')
        return None, None, None, None
    shops_df = generate_shops()
    cashes_df = generate_cashes(shops_df)
    all_receipts = []
    all_receipt_items = []
    for _, cash_row in cashes_df.iterrows():
        shop_id = cash_row['shop_id']
        cash_id = cash_row['cash_id']
        num_receipts_for_cash = randint(1, MAX_RECEIPTS_PER_CASH)
        for _ in range(num_receipts_for_cash):
            receipt, items = generate_receipt(shop_id, cash_id) #, target_date)
            all_receipts.append(receipt)
            all_receipt_items.extend(items)
    return pd.DataFrame(all_receipts), pd.DataFrame(all_receipt_items), shops_df, cashes_df


def generate_data(): ###########
    receipts_df, items_df, shops_df, cashes_df = generate_daily_data() ########
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
