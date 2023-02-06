

class DataManager(object):
    def __init__(self) -> None:
        pass

    def save_message(self, message):
        raise NotImplementedError("Class should implement the method")
    
    def get_messages(self, group_id, message_count=10):
        raise NotImplementedError("Class should implement the method")
    
    def get_group(self, group_id):
        raise NotImplementedError("Class should implement the method")
    
