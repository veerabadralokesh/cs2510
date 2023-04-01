
import threading
import os
import json
import logging
import copy
import server.constants as C
from server.storage.data_manager import DataManager
from server.storage.file_manager import FileManager
from server.storage.utils import is_valid_message, get_timestamp, get_unique_id

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

    def __init__(self, file_manager: FileManager, messages={}, users={}, groups={}) -> None:
        # messages = {message_object, }
        super().__init__()
        self._lock = threading.Lock()
        self.messages = ServerCollection(messages)
        self.sessions = ServerCollection(users)
        self.groups = ServerCollection(groups)
        self.loaded_data = False
        self.file_manager = file_manager
        self.recover_data_from_disk()

    def save_message(self, message):
        """
        saves new msgs, updates msgs and likes unlikes them
        """
        if not is_valid_message(message):
            raise Exception("Invalid Message")
        message_id = message['message_id']
        group_id = message["group_id"]
        message["creation_time"] = int(message["creation_time"])

        if message["message_type"] in (C.NEW, C.USER_JOIN, C.USER_LEFT):
            with self._lock:
                self.messages[message_id] = message
                message["likes"] = {}
                # if group_id not in self.groups:
                #     self.create_group(group_id)
                self.groups[group_id]["message_ids"].append(message_id)
                self.file_manager.append(f'{group_id}_messages.txt', message)

        # elif message["message_type"] in C.APPEND_TO_CHAT_COMMANDS:
        #     with self._lock:
        #         original_message = self.messages[message_id]
        #         original_message["text"].extend(message["text"])
        #         self.groups[group_id]["updated_ids"].append(message_id)
        #         self.file_manager.append(f'{group_id}_messages.txt', original_message)
        else:
            # like / unlike message_type
            with self._lock:
                original_message = self.messages[message_id]
                for key, val in message["likes"].items():
                    if original_message["user_id"] == key:
                        return
                    original_message["likes"][key] = val
                self.groups[group_id]["updated_ids"].append(message_id)
                self.file_manager.append(f'{group_id}_messages.txt', original_message)

        return message
            
    def save_session_info(self, session_id, user_id, group_id=None, is_active=True, context=None):
        session = {
            "session_id": session_id, 
            "user_id": user_id,
            "group_id": group_id,
            "timestamp": get_timestamp(),
            "is_active": is_active,
            "context": context
        }
        self.sessions[session_id] = session

    def get_session_info(self, session_id):
        return self.sessions.get(session_id)

    def get_message_list(self, message_ids):
        """
        helper function for get_messages 
        """
        message_list = []
        for message_id in message_ids:
            message = self.messages.get(message_id)
            if message is not None:
                message_list.append(message)
        return message_list
    
    def get_messages(self, group_id, start_index=-10, updated_idx=None):
        """
        called when user wants to quits history or newly joins
        """
        group = self.get_group(group_id)
        if group is None:
            return []

        with self._lock:
            all_msg_ids = group.get('message_ids')
            message_ids = all_msg_ids[start_index:]
            last_index = len(all_msg_ids)
            updated_ids = None
            if updated_idx is not None:
                updated_ids = group.get('updated_ids')[updated_idx:]
                message_ids.extend(updated_ids)
            updated_idx = len(group.get('updated_ids'))

        return last_index, self.get_message_list(message_ids), updated_idx
    
    def get_group(self, group_id):
        return self.groups.get(group_id)
    
    def create_group(self, group_id, users=[], creation_time=get_timestamp()):
        group = {
            'group_id': group_id,
            'users': users,
            'message_ids': [],
            'creation_time': creation_time,
            'updated_ids': []
        }
        self.groups[group_id] = group
        logging.info(f"Group {group_id} created")
        self.file_manager.write(f'{group_id}.json', group)
        return group

    def add_user_to_group(self, group_id, user_id):
        # print("inside add_user_to_group group id", group_id, "users", user_id)
        self.groups[group_id]['users'].append(user_id)
        logging.info(f"{user_id} joined {group_id}")
        # self.save_message({"group_id": group_id, 
        # "user_id": user_id,
        # "creation_time": get_timestamp(),
        # "message_id": get_unique_id(),
        # "text":[],
        # "message_type": C.USER_JOIN})
    
    def remove_user_from_group(self, group_id, user_id):
        if user_id not in self.groups[group_id]['users']:
            return
        index = self.groups[group_id]['users'].index(user_id)
        del self.groups[group_id]['users'][index]
        logging.info(f"{user_id} removed from {group_id}")

    def recover_data_from_disk(self):
        all_files = self.file_manager.list_files()
        json_files = [f for f in all_files if f.endswith('.json')]
        for file in json_files:
            group_data = json.loads(self.file_manager.read(file))
            self.groups[group_data['group_id']] = group_data

        txt_files = [f for f in all_files if f.endswith('.txt')]
        for file in txt_files:
            messages = self.file_manager.read(file).split('\n')
            message_ids = {}
            for message in messages:
                try:
                    message_data = json.loads(message)
                    message_id = message_data['message_id']
                    group_id = message_data['group_id']
                    if message_id not in message_ids:
                        message_ids[message_id] = 1
                        self.groups[group_id]['message_ids'].append(message_id)
                    self.messages[message_id] = message_data
                except json.decoder.JSONDecodeError:
                    pass

    # def __del__(self):
    #     self.save_on_file()
    
    # def load_from_file(self):
    #     logging.info('loading data from file system')
    #     if C.STORE_DATA_ON_FILE_SYSTEM and os.path.isfile(C.DATA_STORE_FILE_PATH):
    #         with open(C.DATA_STORE_FILE_PATH) as rf:
    #             server_data = json.load(rf)
    #             self.messages = ServerCollection(server_data.get("messages", {}))
    #             self.sessions = ServerCollection(server_data.get("sessions", {}))
    #             self.groups = ServerCollection(server_data.get("groups", {}))
    #             self.loaded_data = True

    # def save_on_file(self):
    #     logging.info("saving data on file system")
    #     try:
    #         if C.STORE_DATA_ON_FILE_SYSTEM and self.loaded_data:
    #             server_data = {
    #                 'messages': self.messages.get_dict(),
    #                 'sessions': self.sessions.get_dict(),
    #                 'groups': self.groups.get_dict(),
    #             }
    #             with open(C.DATA_STORE_FILE_PATH, 'w') as wf:
    #                 json.dump(server_data, wf)
    #     except Exception as e:
    #         pass


# data_store = Datastore()

