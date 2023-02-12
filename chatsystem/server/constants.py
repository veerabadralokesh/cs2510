
import os

STORE_DATA_ON_FILE_SYSTEM = True

DATA_STORE_FILE_DIR_PATH = os.path.join(os.path.expanduser('~'), 'data', 'chat_server')

os.makedirs(DATA_STORE_FILE_DIR_PATH, exist_ok=True)

DATA_STORE_FILE_PATH = os.path.join(DATA_STORE_FILE_DIR_PATH, 'server_datastore.json')

LOG_FILE_PATH = '/tmp/chat_server.log'

CONNECTION_COMMANDS = ['c']
LOGIN_COMMANDS = ['u']
JOIN_GROUP_COMMANDS = ['j']
EXIT_APP_COMMANDS = ['q']
APPEND_TO_CHAT_COMMANDS = ['a']
LIKE_COMMANDS = ['l']
UNLIKE_COMMANDS = ['r']
NEW = 'new'