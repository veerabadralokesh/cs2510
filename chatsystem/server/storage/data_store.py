
import threading
import os
import json
import logging
import copy
import server.constants as C
from server.storage.data_manager import DataManager
from server.storage.utils import is_valid_message

class ServerCollection():
    def __init__(self, initial={}):
        self._lock = threading.Lock()
        self._state = copy.deepcopy(initial)

    def __setitem__(self, key, value):
        with self._lock:
            self._state[key] = value

    def __getitem__(self, key):
        return self._state[key]

    def __contains__(self, key):
        print(key, self._state)
        return (key in self._state)

    def __str__(self) -> str:
        return self._state.__str__()

    def get(self, key):
        return self._state.get(key)
    
    def get_dict(self):
        return self._state

# global state
# state = ServerCollection()

class Datastore(DataManager):

    def __init__(self, messages={}, users={}, groups={}) -> None:
        super().__init__()
        self.messages = ServerCollection(messages)
        self.users = ServerCollection(users)
        self.groups = ServerCollection(groups)
        self.load_from_file()

    def save_message(self, message):
        if not is_valid_message(message):
            raise Exception("Invalid Message")
        message_id = message['message_id']
        if message_id not in self.messages:
            self.messages[message_id] = message
        return True

    def get_message_list(self, message_ids):
        message_list = []
        for message_id in message_ids:
            message = self.messages.get(message_id)
            if message is not None:
                self.message_list.append(message)
        return message_list
    
    def get_messages(self, group_id, message_count=10):
        if message_count < 0: return []
        group = self.get_group(group_id)
        message_ids = group.get('message_ids')[-message_count:]
        return self.get_message_list(message_ids)
    
    def get_group(self, group_id):
        raise NotImplementedError("Class should implement the method")
    
    def __del__(self):
        self.save_on_file()
    
    def load_from_file(self):
        logging.info('loading data from file system')
        if C.STORE_DATA_ON_FILE_SYSTEM and os.path.isfile(C.DATA_STORE_FILE_PATH):
            with open(C.DATA_STORE_FILE_PATH) as rf:
                server_data = json.load(rf)
                self.messages = ServerCollection(server_data.get("messages", {}))
                self.users = ServerCollection(server_data.get("users", {}))
                self.groups = ServerCollection(server_data.get("groups", {}))
    
    def save_on_file(self):
        logging.info("saving data on file system")
        if C.STORE_DATA_ON_FILE_SYSTEM:
            server_data = {
                'messages': self.messages.get_dict(),
                'users': self.users.get_dict(),
                'groups': self.groups.get_dict(),
            }
            with open(C.DATA_STORE_FILE_PATH, 'w') as wf:
                json.dump(server_data, wf)


data_store = Datastore()

