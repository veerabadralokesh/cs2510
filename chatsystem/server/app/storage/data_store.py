
from app.storage.data_manager import DataManager
from app.storage.utils import is_valid_message


class Datastore(DataManager):

    def __init__(self) -> None:
        super().__init__()
        self.messages = {}
        self.users = {}
        self.groups = {}

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


data_store = Datastore()

