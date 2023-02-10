

import logging
import grpc
from concurrent import futures

import chat_system_pb2
import chat_system_pb2_grpc

from server.storage.data_store import Datastore
from google.protobuf.json_format import MessageToDict
from server.storage.utils import is_valid_message

data_store = Datastore()

def get_messages():
    return []

def get_group_details(group_id, user_id):
    logging.info(f"{user_id} joined {group_id}")
    group_details = chat_system_pb2.GroupDetails(group_id=group_id, users=["user1", user_id], status=True)
    return group_details

class ChatServerServicer(chat_system_pb2_grpc.ChatServerServicer):

    def __init__(self, data_store) -> None:
        super().__init__()
        self.data_store = data_store
        pass

    def GetUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Login request form user: {user_id}")
        status = chat_system_pb2.Status(status=True, statusMessage="")

        return status
    
    def LogoutUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Logout request form user: {user_id}")
        status = chat_system_pb2.Status(status=True, statusMessage="")

        return status
    
    def GetGroup(self, request, context):
        group_id = request.group_id
        user_id = request.user_id
        group_details = get_group_details(group_id, user_id)
        return group_details

    def ExitGroup(self, request, context):
        group_id = request.group_id
        user_id = request.user_id
        status = chat_system_pb2.Status(status=True, statusMessage="")
        logging.info(f"{user_id} exited from group {group_id}")
        return status

    def GetMessages(self, request, context):
        prev_messages = []
        for new_message in data_store.get_messages(request.group_id):
            yield new_message
    
    def PostMessage(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        message = MessageToDict(request, preserving_proto_field_name=True)
        data_store.save_message(message)
        return status
    
    def HealthCheck(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        return status


def serve():
    data_store = None
    try:
        data_store = Datastore()
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_system_pb2_grpc.add_ChatServerServicer_to_server(
            ChatServerServicer(data_store), server
        )
        server.add_insecure_port('[::]:12000')
        server.start()
        print("Server started")
        server.wait_for_termination()
    finally:
        if data_store is not None:
            data_store.save_on_file()


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    serve()
