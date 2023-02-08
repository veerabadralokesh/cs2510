
import os

STORE_DATA_ON_FILE_SYSTEM = True

DATA_STORE_FILE_DIR_PATH = os.path.join(os.path.expanduser('~'), 'data', 'chat_server')

os.makedirs(DATA_STORE_FILE_DIR_PATH, exist_ok=True)

DATA_STORE_FILE_PATH = os.path.join(DATA_STORE_FILE_DIR_PATH, 'server_datastore.json')

