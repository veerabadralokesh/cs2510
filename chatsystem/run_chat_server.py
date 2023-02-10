

import logging
import grpc
from concurrent import futures
import threading
import chat_system_pb2
import chat_system_pb2_grpc

from server.storage.data_store import Datastore
from google.protobuf.json_format import MessageToDict
from server.storage.utils import is_valid_message
import server.constants as C

data_store = Datastore()

def get_messages():
    return []

def get_group_details(group_id, user_id):

    if not data_store.get_group(group_id):
        data_store.create_group(group_id)

    data_store.add_user_to_group(group_id, user_id)

    group_details = chat_system_pb2.GroupDetails(group_id=group_id, users=["user1", user_id], status=True)
    return group_details


class ChatServerServicer(chat_system_pb2_grpc.ChatServerServicer):

    def __init__(self, data_store) -> None:
        super().__init__()
        self.data_store = data_store
        self.new_message_event = threading.Event()

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
        data_store.remove_user_from_group(group_id, user_id)
        status = chat_system_pb2.Status(status=True, statusMessage="")
        logging.info(f"{user_id} exited from group {group_id}")
        return status

    def GetMessages(self, request, context):
        prev_messages = []
        chat_index = 0
        print("enter get messages")
        while True:
            print("message in group", request.group_id, ":", data_store.get_messages(request.group_id))
            for new_message in data_store.get_messages(request.group_id):

                if len(data_store.get_messages(request.group_id)) > chat_index:
                    chat_index += 1
                    message_grpc = chat_system_pb2.Message(
                        group_id=new_message["group_id"],
                        user_id=new_message["user_id"],
                        creation_time=new_message["creation_time"],
                        text=new_message["text"],
                        message_id=new_message["message_id"],
                        likes=new_message.get("likes"),
                        message_type=new_message["message_type"]
                    )

                    yield message_grpc

            self.new_message_event.clear()
            print("check 1")
            self.new_message_event.wait()
            print("check 2")

    
    def PostMessage(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        message = MessageToDict(request, preserving_proto_field_name=True)
        data_store.save_message(message)
        self.new_message_event.set()
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
