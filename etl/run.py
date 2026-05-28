#from datetime import datetime
from dotenv import load_dotenv
from etl.export_to_db import from_minio_to_db
from generator.gen_sales import export_to_minio, generate_data
from storage.minio_client import MinIOClient
from storage.pgdb import PGDatabase
from utils.logger import get_logger
from utils.tg_handler import send_to_tg

logger = get_logger(__name__)

load_dotenv()

#
# def test_all_weekdays():
#     for i in range(7):
#         test_date = datetime(2024, 1, i + 1)
#         print(f'Запуск за {test_date.strftime("%A %Y-%m-%d")}')
#         try:
#             main(test_date)
#         except Exception as e:
#             print(f'Ошибка: {e}')


def main(): #########
    logger.info('Pipeline started')
    send_to_tg('Generating has been started')

    receipts_df, items_df, shops_df, cashes_df = generate_data() ###########

    if receipts_df is None:
        logger.info('Pipeline skipped on Sunday')
        send_to_tg('Pipeline skipped on Sunday')
        return

    minio = MinIOClient()

    logger.info(f'Generated shops: {len(shops_df)}, '
                f'Cashes: {len(cashes_df)}, '
                f'Receipts: {len(receipts_df)}, '
                f'Items: {len(items_df)}')
    send_to_tg(f'Generated:\n'
               f'Shops: {len(shops_df)},\n'
               f'Cashes: {len(cashes_df)},\n'
               f'Receipts: {len(receipts_df)},\n'
               f'Items: {len(items_df)}')

    with PGDatabase() as db:
        try:
            db.insert_shop(shops_df)
            db.insert_cashes(cashes_df)
            db.insert_receipts(receipts_df)
            db.insert_receipt_items(items_df)
            db.conn.commit()
        except Exception:
            db.conn.rollback()
            raise

    export_to_minio(receipts_df, items_df, minio)
    from_minio_to_db(minio)
    logger.info('Pipeline finished')
    send_to_tg('Pipeline finished')


if __name__ == '__main__':
    #test_all_weekdays()
    main()
