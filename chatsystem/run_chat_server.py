
import argparse
import logging
import threading
from concurrent import futures
import copy
import chat_system_pb2
import chat_system_pb2_grpc
import grpc
import server.constants as C
from google.protobuf.json_format import MessageToDict
from server.storage.data_store import Datastore, ServerCollection
from server.storage.file_manager import FileManager
from server.storage.utils import get_unique_id, get_timestamp, clean_message
from server.server_pool_manager import ServerPoolManager

# data_store = Datastore()


class ChatServerServicer(chat_system_pb2_grpc.ChatServerServicer):

    def __init__(self, data_store: Datastore, spm: ServerPoolManager, file_manager: FileManager, server_id) -> None:
        super().__init__()
        self.data_store = data_store
        # self.new_message_event = threading.Event()
        self._lock = threading.Lock()
        self.timestamp_lock = threading.Lock()
        self.group_message_events = ServerCollection()
        self.spm = spm
        self.file_manager = file_manager
        self.server_id = server_id
        self.spm.register_callback(C.SERVER_DIED_CALLBACK, self.remove_group_participants_server_disconnected)

    def remove_group_participants_server_disconnected(self, server_id):
        logging.info(f'server died {server_id}')
        event_group_ids = self.data_store.remove_group_participants_server_disconnected(server_id=server_id)
        # logging.info(f'{event_group_ids} events')
        for group_id in event_group_ids:
            self.group_message_events[group_id].set()
    
    def get_group_message_event(self, group_id):
        event = self.group_message_events.get(group_id)
        if event:
            return event
        else:
            with self._lock:
                if group_id not in self.group_message_events:
                    self.group_message_events[group_id] = threading.Event()
                return self.group_message_events[group_id]

    def get_group_details(self, group_id: str, user_id: str) -> chat_system_pb2.GroupDetails:

        group_created=False
        if not self.data_store.get_group(group_id):
            group = self.data_store.create_group(group_id)
            group_created = True
            
        self.data_store.add_user_to_group(group_id, user_id, server_id = self.server_id)

        if group_created:
            server_message = {
                "group_id": group_id,
                # "users": group.get('users', {}),
                "creation_time": group.get('creation_time', self.get_timestamp())
            }
            self.spm.send_msg_to_connected_servers(server_message, event_type=C.GROUP_EVENT)

        group = self.data_store.get_group(group_id)
        users_list = self.data_store.expand_user_list(group_id, group.get('updated_time'))
        group_details = chat_system_pb2.GroupDetails(
            group_id=group_id, 
            users=users_list, 
            status=True
            )
        return group_details

    def GetUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Login request from user: {user_id}")
        session_id = get_unique_id()
        status = chat_system_pb2.Status(status=True, statusMessage=session_id)
        self.data_store.save_session_info(session_id, user_id)
        return status
    
    def LogoutUser(self, request, context):
        user_id = request.user_id
        logging.info(f"Logout request from user: {user_id}")
        status = chat_system_pb2.Status(status=True, statusMessage="")
        self.data_store.save_session_info(request.session_id, user_id, is_active=False)
        return status
    
    def GetGroup(self, request, context):
        group_id = request.group_id
        user_id = request.user_id
        group_details = self.get_group_details(group_id, user_id)
        # logging.info(f"{user_id} joined {group_id}")
        self.new_message({"group_id": group_id, 
        "user_id": user_id,
        "creation_time": self.get_timestamp(),
        "message_id": get_unique_id(),
        "text":[],
        "message_type": C.USER_JOIN})
        # self.new_message_event.set()
        self.data_store.save_session_info(request.session_id, user_id, group_id)
        return group_details

    def ExitGroup(self, request, context):
        group_id = request.group_id
        user_id = request.user_id
        session_id = request.session_id
        group = self.data_store.remove_user_from_group(group_id, user_id, server_id=self.server_id)
        status = chat_system_pb2.Status(status=True, statusMessage="")
        logging.info(f"{user_id} exited from group {group_id}")
        self.new_message({"group_id": group_id, 
        "user_id": user_id,
        "creation_time": get_timestamp(),
        "message_id": get_unique_id(),
        "text":[],
        "message_type": C.USER_LEFT})
        self.data_store.save_session_info(session_id, user_id, is_active=True)

        # server_message = {
        #     "group_id": group_id,
        #     "users": group.get('users', []),
        #     "creation_time": group.get('creation_time'),
        # }
        # self.spm.send_msg_to_connected_servers(server_message, event_type=C.GROUP_EVENT)
        

        # self.new_message_event.set()
        self.get_group_message_event(group_id).set()
        self.data_store.save_session_info(request.session_id, user_id)
        return status

    def GetMessages(self, request, context):
        prev_messages = []
        last_msg_idx = request.message_start_idx
        updated_idx = None

        user_id = request.user_id
        group_id = request.group_id
        session_id = request.session_id

        self.data_store.save_session_info(session_id, user_id=user_id, group_id=group_id, context=context)

        while True:
            if not context.is_active():
                session_info = self.data_store.get_session_info(session_id)
                if session_info["group_id"] == group_id:
                    session_info = self.data_store.get_session_info(session_id)
                    if session_info.get('context') and not session_info.get('context').is_active():
                        self.data_store.remove_user_from_group(group_id, user_id, server_id=self.server_id)
                        self.data_store.save_session_info(session_id, user_id, is_active=False)
                        # self.new_message_event.set()
                        self.get_group_message_event(group_id).set()
                break
            updated_idx, new_messages = self.data_store.get_messages(group_id, start_index=last_msg_idx, change_log_index=updated_idx)
            
            last_msg_idx = 1
            
            for new_message in new_messages:
                # print(new_message)
                message_grpc = chat_system_pb2.Message(
                    group_id=new_message.get("group_id", group_id),
                    user_id=new_message.get("user_id"),
                    users=new_message.get("users"),
                    creation_time=new_message.get("creation_time"),
                    text=new_message.get("text", []),
                    message_id=new_message.get("message_id"),
                    likes=new_message.get("likes"),
                    message_type=new_message["message_type"],
                    previous_message_id=new_message.get('previous_message_id')
                )

                yield message_grpc

            # self.new_message_event.clear()
            # self.new_message_event.wait()
            self.get_group_message_event(group_id).clear()
            self.get_group_message_event(group_id).wait()


    def new_message(self, message):
        message['vector_timestamp'] = self.spm.update_vector_timestamp()
        clean_message(message)
        
        server_message = self.data_store.save_message(message)
        # print('server_message', server_message)
        if server_message:
            self.spm.send_msg_to_connected_servers(server_message)
            # self.new_message_event.set()
            group_id = message.get("group_id")
            if group_id:
                self.get_group_message_event(group_id).set()

    def get_timestamp(self):
        with self.timestamp_lock:
            return get_timestamp()

    def PostMessage(self, request, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        message = MessageToDict(request, preserving_proto_field_name=True)
        # add vector timestamp to message
        message['server_id'] = self.server_id
        message['creation_time'] = self.get_timestamp()
        self.new_message(message)
        return status
    
    def HealthCheck(self, request_iter, context):
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        session_id = None
        try:
            for request in request_iter:
                session_id = request.session_id
        except Exception:
            if session_id is not None:
                session_info = self.data_store.get_session_info(session_id)
                # if session_info.get('context') and not session_info.get('context').is_active():
                group_id, user_id = session_info.get('group_id'), session_info.get('user_id')
                if group_id is not None:
                    self.new_message({"group_id": group_id, 
                    "user_id": user_id,
                    "creation_time": self.get_timestamp(),
                    "message_id": get_unique_id(),
                    "text":[],
                    "message_type": C.USER_LEFT})
                    self.data_store.remove_user_from_group(group_id, user_id, server_id=self.server_id)
                    self.data_store.save_session_info(session_id, user_id, is_active=False)
                    # self.new_message_event.set()
                    self.get_group_message_event(group_id).set()
        return status
    
    def Ping(self, request, context):
        # print(request)
        message = MessageToDict(request, preserving_proto_field_name=True)
        server_id = message['server_id']
        server_view = message.get('server_view', None)
        server_timestamps = message.get('server_timestamps', None)
        replay_server_id = message.get('replay_server_id', '0')
        # print(server_id, server_timestamps)
        if server_id and server_view and server_timestamps:
            self.spm.send_msg_to_recovered_servers(server_id, server_view, server_timestamps, replay_server_id)
            # if replay_server_id != '0':
            #     logging.info('returning from Ping')
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        return status

    def GetServerView(self, request, context):
        status = chat_system_pb2.Status(
            status=True, 
            statusMessage = ", ".join(list(map(str, self.spm.get_connected_servers_view())))
            )
        return status

    def SyncMessagetoServer(self, request, context):
        """getting messages from other servers"""
        # whenever new message comes from client,
        # send it to spm, which is connected to other servers
        # then send
        status = chat_system_pb2.Status(status=True, statusMessage = "")
        message = MessageToDict(request, preserving_proto_field_name=True)
        clean_message(message)
        message_copy = copy.deepcopy(message)
        event_type = message['event_type']
        message_type = message.get('message_type')
        group_id = message.get('group_id')
        user_id = message.get('user_id')
        incoming_server_id = message["server_id"]

        # logging.info('msg received')

        self.spm.update_vector_timestamp(message)

        if event_type == C.MESSAGE_EVENT:
            # add vector timestamp to message
            self.data_store.save_message(message)
            if message_type == C.USER_LEFT:
                self.data_store.remove_user_from_group(group_id, user_id, server_id=incoming_server_id)
            if message_type == C.USER_JOIN:
                self.data_store.add_user_to_group(group_id, user_id, server_id=incoming_server_id)
            # trigger new message event i.e. calling getmessages
            # self.new_message_event.set()
            self.get_group_message_event(group_id).set()
            self.spm.log_message(message_copy)
        elif event_type == C.GROUP_EVENT:
            users = message.get('users', {})
            creation_time = message.get('creation_time')
            if not self.data_store.get_group(group_id):
                # print(f'creating group {group_id}')
                self.data_store.create_group(group_id, users, creation_time)
            self.spm.log_message(message_copy)
        elif event_type == C.GET_GROUP_META_DATA:
            all_groups_data = self.data_store.get_groups_meta_data()
            for group_meta in all_groups_data:
                # print('group_meta: ', group_meta)
                self.spm.send_to_server(group_meta, target_server_id=incoming_server_id, event_type=C.GROUP_META_DATA)
        elif event_type == C.GROUP_META_DATA:
            group_meta_data = message
            
            if self.data_store.update_group_meta_data(group_id, group_meta_data, incoming_server_id):
                self.get_group_message_event(group_id).set()
        else:
            raise Exception('Unknown event type')
        return status

def get_args():
    parser = argparse.ArgumentParser(description="Script for running CS 2510 Project 2 servers")
    parser.add_argument('-id', type=str, help='Server Number', required=True)
    args = parser.parse_args()
    print(args)
    return args


def serve():
    data_store = None
    args = get_args()
    if args.id not in C.SERVER_IDS:
        raise Exception("Invalid server id")
    try:
        file_manager = FileManager(root=C.DATA_STORE_FILE_DIR_PATH.format(args.id))
        data_store = Datastore(file_manager, server_id=args.id)
        spm = ServerPoolManager(args.id, file_manager, data_store)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10000))
        chat_system_pb2_grpc.add_ChatServerServicer_to_server(
            ChatServerServicer(data_store, spm, file_manager, args.id), server
        )
        if C.USE_DIFFERENT_PORTS:
            id = int(args.id)
            server.add_insecure_port(f'[::]:{(11999+id)}')
            print(f"Server [::]:{(11999+id)} started")
        else:
            server.add_insecure_port('[::]:12000')
            print("Server started")
        server.start()
        
        server.wait_for_termination()
    finally:
        pass
        # if data_store is not None:
            # data_store.save_on_file()


if __name__ == '__main__':
    # logging.basicConfig()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    serve()
