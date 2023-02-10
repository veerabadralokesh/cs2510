

RECONNECT = 'RECONNECT'

EXIT_CODE = 'EXIT_CODE'

SWITCH_GROUP = 'SWITCH_GROUP'

ACTIVE_USER_KEY = 'active_user_id'
ACTIVE_GROUP_KEY = 'active_group_id'
ACTIVE_CHANNEL = 'channel'

GROUP_DATA = 'group_data'

CONNECTION_COMMANDS = ['c']
LOGIN_COMMANDS = ['u']
JOIN_GROUP_COMMANDS = ['j']
EXIT_APP_COMMANDS = ['q']

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
