

import logging
import threading
from concurrent import futures

import chat_system_pb2
import chat_system_pb2_grpc
import grpc
import server.constants as C
from google.protobuf.json_format import MessageToDict
from server.storage.data_store import Datastore
from server.storage.utils import get_unique_id

data_store = Datastore()

def get_messages():
    return []

def get_group_details(group_id: str, user_id: str) -> chat_system_pb2.GroupDetails:

    if not data_store.get_group(group_id):
        data_store.create_group(group_id)

    data_store.add_user_to_group(group_id, user_id)

    group_details = chat_system_pb2.GroupDetails(group_id=group_id, users=data_store.get_group(group_id)["users"], status=True)
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
        session_id = get_unique_id()
        status = chat_system_pb2.Status(status=True, statusMessage="")
        data_store.save_session_info(session_id, user_id)
        return status
    
    def LogoutUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Logout request form user: {user_id}")
        status = chat_system_pb2.Status(status=True, statusMessage="")
        data_store.save_session_info(request.session_id, user_id, is_active=False)
        return status
    
    def GetGroup(self, request, context):
        print("inside get group")
        group_id = request.group_id
        user_id = request.user_id
        group_details = get_group_details(group_id, user_id)
        self.new_message_event.set()
        data_store.save_session_info(request.session_id, user_id, group_id)
        return group_details

    def ExitGroup(self, request, context):
        group_id = request.group_id
        user_id = request.user_id
        data_store.remove_user_from_group(group_id, user_id)
        status = chat_system_pb2.Status(status=True, statusMessage="")
        logging.info(f"{user_id} exited from group {group_id}")
        self.new_message_event.set()
        data_store.save_session_info(request.session_id, user_id)
        return status

    def GetMessages(self, request, context):
        prev_messages = []
        # print("enter get messages")
        last_msg_idx = request.message_start_idx
        updated_idx = None

        while True:
            if not context.is_active():
                session_info = data_store.get_session_info(request.session_id)
                if session_info["group_id"] == request.group_id:
                    data_store.remove_user_from_group(request.group_id, request.user_id)
                    data_store.save_session_info(request.session_id, request.user_id, is_active=False)
                    self.new_message_event.set()
                break
            # print("message in group", request.group_id, ":", data_store.get_messages(request.group_id))
            last_msg_idx, new_messages, updated_idx = data_store.get_messages(request.group_id, start_index=last_msg_idx, updated_idx=updated_idx)
            print("updated_idx",updated_idx)
            for new_message in new_messages:
                
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
            self.new_message_event.wait()
        print("User switched group")
        # create message ("User ID" left the chat)


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
