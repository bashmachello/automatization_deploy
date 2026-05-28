import logging
import os
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt

load_dotenv()


class TelegramHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def emit(self, record):
        try:
            message = self.format(record)
            requests.post(f'https://api.telegram.org/bot{self.token}/sendMessage',
                          json={'chat_id': self.chat_id,
                                'text': message},
                          timeout=5)
        except Exception:
            pass


@retry(stop=stop_after_attempt(3))
def send_to_tg(text):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    try:
        requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id': chat_id,
                            'text': text},
                      timeout=5)
    except Exception as e:
        print(e)
        raise
