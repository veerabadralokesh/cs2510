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
GET_SERVER_VIEW_COMMANDS = ['v']

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
PARTICIPANT_LIST = 'PARTICIPANT_LIST'

INPUT_PROMPT = "Enter command"
NEW_MESSAGE_SCROLL = "New message arrived, scrolling to the bottom"
SCROLL_REACHED_BOTTOM = "Reached bottom of messages"
SCROLL_REACHED_TOP = "Reached top of messages"

NEGATIVE_MESSAGE_INDEX = 'NEGATIVE_MESSAGE_INDEX'

INIT_MESSAGES = {
    0: "Commands",
    1: "c {server address:port}\t connect to server",
    2: "u {username}\t\t login with username",
    3: "j {group}\t\t join group",
    4: "a {message}\t\t send message in the group",
    5: "l {message_id}\t\t like the message with message_id",
    6: "r {message_id}\t\t remove like for the message with message_id",
    7: "p \t\t\t print message history of the group",
    8: "v \t\t\t print server's current view of which servers it can currently communicate with",
    9: "q \t\t\t Quit"
}