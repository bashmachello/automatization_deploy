import logging
import os
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt

load_dotenv()

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3))
def send_to_tg(text):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logger.warning('Telegram token or chat id not set')
        return
    try:
        response  = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id': chat_id,
                            'text': text},
                      timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")
