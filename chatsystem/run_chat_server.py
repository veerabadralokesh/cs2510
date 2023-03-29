
import argparse
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
from server.server_pool_manager import ServerPoolManager

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

    def __init__(self, data_store, spm) -> None:
        super().__init__()
        self.data_store = data_store
        self.new_message_event = threading.Event()
        self.spm = spm
        pass

    def GetUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Login request form user: {user_id}")
        session_id = get_unique_id()
        status = chat_system_pb2.Status(status=True, statusMessage=session_id)
        data_store.save_session_info(session_id, user_id)
        return status
    
    def LogoutUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Logout request form user: {user_id}")
        status = chat_system_pb2.Status(status=True, statusMessage="")
        data_store.save_session_info(request.session_id, user_id, is_active=False)
        return status
    
    def GetGroup(self, request, context):
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
        last_msg_idx = request.message_start_idx
        updated_idx = None

        user_id = request.user_id
        group_id = request.group_id
        session_id = request.session_id

        data_store.save_session_info(session_id, user_id=user_id, group_id=group_id, context=context)

        while True:
            if not context.is_active():
                session_info = data_store.get_session_info(session_id)
                if session_info["group_id"] == group_id:
                    session_info = data_store.get_session_info(session_id)
                    if session_info.get('context') and not session_info.get('context').is_active():
                        data_store.remove_user_from_group(group_id, user_id)
                        data_store.save_session_info(session_id, user_id, is_active=False)
                        self.new_message_event.set()
                break
            last_msg_idx, new_messages, updated_idx = data_store.get_messages(group_id, start_index=last_msg_idx, updated_idx=updated_idx)
            
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


    def PostMessage(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        message = MessageToDict(request, preserving_proto_field_name=True)
        data_store.save_message(message)
        self.new_message_event.set()
        return status
    
    def HealthCheck(self, request_iter, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        session_id = None
        try:
            for request in request_iter:
                session_id = request.session_id
        except Exception:
            if session_id is not None:
                session_info = data_store.get_session_info(session_id)
                # if session_info.get('context') and not session_info.get('context').is_active():
                group_id, user_id = session_info.get('group_id'), session_info.get('user_id')
                if group_id is not None:
                    data_store.remove_user_from_group(group_id, user_id)
                    data_store.save_session_info(session_id, user_id, is_active=False)
                    self.new_message_event.set()
            pass
        return status
    
    def Ping(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        return status

    def SendMessagetoServer(self):
        # whenever new message comes from client,
        # send it to all connected servers
        
        pass

def get_args():
    parser = argparse.ArgumentParser(description="Script for running CS 2510 Project 2 servers")
    parser.add_argument('-id', type=int, help='Server Number', required=True)
    args = parser.parse_args()
    print(args)
    return args


def serve():
    data_store = None
    args = get_args()
    try:
        data_store = Datastore()
        spm = ServerPoolManager(id=args.id)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10000))
        chat_system_pb2_grpc.add_ChatServerServicer_to_server(
            ChatServerServicer(data_store, spm), server
        )
        if C.USE_DIFFERENT_PORTS:
            id = args.id
            server.add_insecure_port(f'[::]:{(11999+id)}')
            print(f"Server [::]:{(11999+id)} started")
        else:
            server.add_insecure_port('[::]:12000')
            print("Server started")
        server.start()
        
        server.wait_for_termination()
    finally:
        if data_store is not None:
            data_store.save_on_file()


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    serve()
