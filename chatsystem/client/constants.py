SESSION_ID = 'SESSION_ID'

RECONNECT = 'RECONNECT'

EXIT_CODE = 'EXIT_CODE'

SWITCH_GROUP = 'SWITCH_GROUP'

ACTIVE_USER_KEY = 'active_user_id'
ACTIVE_GROUP_KEY = 'active_group_id'
ACTIVE_CHANNEL = 'channel'
MESSAGE_START_IDX = 'MESSAGE_START_IDX'

GROUP_DATA = 'group_data'

CONNECTION_COMMANDS = ['c']
LOGIN_COMMANDS = ['u']
JOIN_GROUP_COMMANDS = ['j']
EXIT_APP_COMMANDS = ['q']
APPEND_TO_CHAT_COMMANDS = ['a']
LIKE_COMMANDS = ['l']
UNLIKE_COMMANDS = ['r']
PRINT_HISTORY_COMMANDS = ['p']

STUB = 'stub'

SERVER_ONLINE = 'server_connection_active'
SERVER_CONNECTION_STRING = 'server_string'

HEALTH_CHECK_INTERVAL = 60
MESSAGE_CHECK_INTERVAL = 1
DEFAULT_SERVER_CONNECTION_STRING = 'localhost:12000'

SERVER_CONNECTION_CHECK = 0
USER_LOGIN_CHECK = 1
JOIN_GROUP_CHECK = 2
SENT_MESSAGE_CHECK = 3

NO_ACTIVE_SERVER = "No active server found, please connect to a server first"
NO_ACTIVE_USER = "No active user, please login using username"
NO_ACTIVE_GROUP = "No active group, please join a group"

TEXT_MSG_IDX = 'TEXT_MSG_IDX'
MESSAGE_ID_TO_NUMBER_MAP = "message_id_to_number_map"
TEXT_ID_TO_NUMBER_MAP = "TEXT_ID_TO_NUMBER_MAP"
MESSAGE_NUMBER_TO_ID_MAP = "message_number_to_id_map"
MESSAGE_NUMBER = "message_number"
MESSAGES = "MESSAGES"
NEW = "new"
USER_JOIN = 'joined'
USER_LEFT = 'left'

INPUT_PROMPT = "Enter command"
NEW_MESSAGE_SCROLL = "New message arrived, scrolling to the bottom"
SCROLL_REACHED_BOTTOM = "Reached bottom of messages"
SCROLL_REACHED_TOP = "Reached top of messages"
