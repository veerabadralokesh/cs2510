
from __future__ import print_function

import curses
import logging
import uuid
import grpc
import chat_system_pb2
import chat_system_pb2_grpc
from time import sleep
from google.protobuf.json_format import MessageToDict
from datetime import datetime
import json
import threading
from threading import Thread
from queue import Queue
from client import constants as C
from client.display_manager_ncurses import DisplayManagerCurses

global state

global display_manager
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
display_manager = DisplayManagerCurses(stdscr)

# display_manager.write(dir(dict))
class ClientState():
    def __init__(self, initial={}):
        self._lock = threading.Lock()
        self._state = initial

    def __setitem__(self, key, value):
        with self._lock:
            self._state[key] = value

    def __getitem__(self, key):
        return self._state[key]

    def __contains__(self, key):
        return (key in self._state)

    def __str__(self) -> str:
        return self._state.__str__()

    def get(self, key):
        return self._state.get(key)
    
    def get_dict(self):
        return self._state

state = ClientState()

# state['a'] = 'b'
# with open('/tmp/test.json1', 'w') as wf:
#     json.dump(state.get_dict(), wf)


def check_state(check_point):
    if check_point > C.SERVER_CONNECTION_CHECK:
        if not state.get(C.SERVER_ONLINE):
            raise Exception(C.NO_ACTIVE_SERVER)
    if check_point > C.USER_LOGIN_CHECK:
        if state.get(C.ACTIVE_USER_KEY) is None:
            raise Exception(C.NO_ACTIVE_USER)
    if check_point > C.JOIN_GROUP_CHECK:
        if state.get(C.ACTIVE_GROUP_KEY) is None:
            raise Exception(C.NO_ACTIVE_GROUP)


def exit_group(user_id, group_id):
    stub=state.get(C.STUB)
    stub.ExitGroup(chat_system_pb2.Group(
        group_id=group_id, user_id=user_id, session_id=state.get(C.SESSION_ID)))
    display_manager.info(
        f"{user_id} successfully exited group {group_id}")
    display_manager.write_header(group_name="",participants="")
    display_manager.reset()
    state[C.ACTIVE_GROUP_KEY] = None
    display_manager.clear()


def logout_user(user_id):
    stub=state.get(C.STUB)
    if state.get(C.ACTIVE_USER_KEY) == user_id:
        exit_group(user_id=user_id,
                    group_id=state[C.ACTIVE_GROUP_KEY])

        stub.LogoutUser(chat_system_pb2.User(user_id=user_id))
        display_manager.info(f"Logout successful for user_id {user_id}")
        display_manager.reset()
        state[C.ACTIVE_USER_KEY] = None


def close_connection(stub=None, channel=None):
    """
    manages 3 exit cases
    channel: 
    1st case: 
    changing group or changing user
    
    """
    if channel is None:
        return
    user_id = state.get(C.ACTIVE_USER_KEY)
    if user_id is not None:
        logout_user(user_id)
    channel.close()
    display_manager.info(
        f"terminated {state[C.SERVER_CONNECTION_STRING]} successfully")
    state[C.ACTIVE_CHANNEL] = None
    state[C.SERVER_ONLINE] = False
    state[C.SERVER_CONNECTION_STRING] = None
    state[C.STUB] = None


def health_check_stream():
    while True:
        yield chat_system_pb2.ActiveSession(session_id=state.get(C.SESSION_ID))
        state[C.USER_JOINED_EVENT].wait()
        state[C.USER_JOINED_EVENT].clear()
        # sleep(C.HEALTH_CHECK_INTERVAL)
    pass

def health_check():
    while True:
        try:
            stub = state.get(C.STUB)
            if stub is not None:
                server_status = stub.HealthCheck(
                    health_check_stream()
                    )
                if server_status.status is True:
                    state[C.SERVER_ONLINE] = True
                else:
                    # display_manager.write("enter", "server_status.status ", server_status.status )
                    state[C.SERVER_ONLINE] = False
            else:
                state[C.SERVER_ONLINE] = False
        except Exception as ex:
            state[C.SERVER_ONLINE] = False
            state[C.ACTIVE_GROUP_KEY] = None
            state[C.ACTIVE_USER_KEY] = None
            display_manager.reset()
            display_manager.error('server disconnected')
        # sleep(C.HEALTH_CHECK_INTERVAL)
        state[C.USER_JOINED_EVENT].wait()
        state[C.USER_JOINED_EVENT].clear()

def cancel_rpc(event, grpc_context):
    event.wait()
    grpc_context.cancel()
    event.clear()
    pass

def update_participants(message, start_timestamp):
    if message.group_id == state.get(C.ACTIVE_GROUP_KEY):
        group_data = state.get(C.GROUP_DATA)
        if group_data is None: return
        participants = group_data['users']
        # print("check 1", participants)
        if message.message_type == C.USER_JOIN:
            if int(message.creation_time) > start_timestamp:
                participants.append(message.user_id)
        elif message.message_type == C.USER_LEFT:
            try:
                if int(message.creation_time) > start_timestamp:
                    index = participants.index(message.user_id)
                    del participants[index]
            except:
                pass
        # print("check 2", participants)
        display_manager.write_header(group_name=f"Group: {state.get(C.ACTIVE_GROUP_KEY)}",
                    participants=f"Participants: {', '.join(set(participants))}")

def get_messages(change_group_event):
    while True:
        stub = state.get(C.STUB)
        if stub is None or state.get(C.ACTIVE_GROUP_KEY) is  None:
            sleep(C.MESSAGE_CHECK_INTERVAL)
            continue
        
        group_id = state.get(C.ACTIVE_GROUP_KEY)
        message_start_idx = state.get(C.MESSAGE_START_IDX)
        user_id = state.get(C.ACTIVE_USER_KEY)
        messages = stub.GetMessages(chat_system_pb2.Group(group_id=group_id, user_id=user_id, message_start_idx=message_start_idx, session_id=state[C.SESSION_ID]))
        cancel_messages_thread = Thread(target=cancel_rpc, args=[change_group_event, messages], daemon=True)
        cancel_messages_thread.start()
        try:
            start_timestamp = get_timestamp()
            for message in messages:
                message_type = message.message_type
                msg_dict = MessageToDict(message, preserving_proto_field_name=True)
                if message_type == C.PARTICIPANT_LIST:
                    existing_participant_set = set(state[C.GROUP_DATA].get('users', []))
                    state[C.GROUP_DATA]['users'] = msg_dict['users']
                    new_participant_set = set(msg_dict['users'])
                    participants_left_set = existing_participant_set - new_participant_set
                    participants_joined_set = new_participant_set - existing_participant_set
                    display_manager.write_header(group_name=f"Group: {state.get(C.ACTIVE_GROUP_KEY)}",
                                                    participants=f"Participants: {', '.join(set(msg_dict['users']))}")
                    info_message = ""
                    if len(participants_left_set) > 0:
                        info_message += " " + ", ".join(participants_left_set) + " left the chat."
                    if len(participants_joined_set) > 0:
                        info_message += " " + ", ".join(participants_joined_set) + " joined the chat. "
                    if len(info_message) > 0:
                        info_message = f'({datetime.fromtimestamp(int(message.creation_time/10**6))})' + info_message
                    display_manager.info(info_message)
                    continue
                if message.message_id not in state[C.MESSAGE_ID_TO_NUMBER_MAP]:
                    state[C.MESSAGE_NUMBER] += 1
                    # this is to look up display line number of message id
                    state[C.MESSAGE_ID_TO_NUMBER_MAP][message.message_id] =  state[C.MESSAGE_NUMBER]

                msg_indx = state[C.MESSAGE_ID_TO_NUMBER_MAP][message.message_id]

                if message.message_type in (C.USER_JOIN, C.USER_LEFT):
                    display_manager.write(msg_indx, f"{message.user_id} {message.message_type} group ({datetime.fromtimestamp(int(message.creation_time/10**6))}).")
                    update_participants(message, start_timestamp)
                    continue
                else:
                    if message.message_id not in state[C.TEXT_ID_TO_NUMBER_MAP]:
                        state[C.TEXT_MSG_IDX] += 1
                        # this map is to look up text message id
                        state[C.MESSAGE_NUMBER_TO_ID_MAP][state[C.TEXT_MSG_IDX]] = message.message_id
                        state[C.TEXT_ID_TO_NUMBER_MAP][message.message_id] = state[C.TEXT_MSG_IDX]

                if msg_dict.get("likes"):
                    count = sum(list(map(int, msg_dict.get("likes").values())))
                else:
                    count = 0
                if count > 0:
                    like_text = f'\t\t\t Likes: {count}'
                else: 
                    like_text = ''
                #  if message_type : 
                text_idx = state[C.TEXT_ID_TO_NUMBER_MAP][message.message_id]
                display_manager.write(msg_indx, f"{text_idx}. {message.user_id}: {' '.join(message.text)}{like_text}")
        except grpc.RpcError as rpc_error:
            display_manager.debug(rpc_error)
        except Exception as e:
            display_manager.error(e)
    
        sleep(C.MESSAGE_CHECK_INTERVAL)


def join_server(server_string):
    if server_string == state.get(C.SERVER_CONNECTION_STRING) and state.get(C.SERVER_ONLINE):
        display_manager.info(f'Already connected to server {server_string}')
        return state.get(C.STUB)
    channel = state.get(C.ACTIVE_CHANNEL)
    if channel and state.get(C.SERVER_ONLINE):
        close_connection(channel)
    display_manager.info(f"Trying to connect to server: {server_string}")
    channel = grpc.insecure_channel(server_string)
    stub = chat_system_pb2_grpc.ChatServerStub(channel)
    # server_status = stub.HealthCheck(chat_system_pb2.ActiveSession(session_id=None))
    # if server_status.status is True:
    display_manager.info("Server connection active")
    state[C.ACTIVE_CHANNEL] = channel
    state[C.SERVER_ONLINE] = True
    state[C.SERVER_CONNECTION_STRING] = server_string
    state[C.STUB] = stub
    # state[C.ACTIVE_GROUP_KEY] = None
    return stub


def get_user_connection(stub, user_id):
    try:
        check_state(C.USER_LOGIN_CHECK)
        if state.get(C.ACTIVE_USER_KEY) is not None:
            if state.get(C.ACTIVE_USER_KEY) != user_id:
                # print(state[C.ACTIVE_USER_KEY])
                logout_user(user_id=state[C.ACTIVE_USER_KEY])
                display_manager.set_user(user_id=C.INPUT_PROMPT)
            else:
                display_manager.info(f"User {user_id} already logged in")
                return
        status = stub.GetUser(chat_system_pb2.User(user_id=user_id))
        state[C.SESSION_ID] = status.statusMessage
        if status.status is True:
            display_manager.info(f"Login successful with user_id {user_id}")
            display_manager.set_user(user_id)
            state[C.ACTIVE_USER_KEY] = user_id
            state[C.USER_JOINED_EVENT].set()
        else:
            raise Exception("Login not successful")
    except grpc.RpcError as rpcError:
        raise rpcError
    except Exception as ex:
        raise ex


def enter_group_chat(stub, group_id, change_group_event):
    try:
        check_state(C.JOIN_GROUP_CHECK)
        current_group_id = state.get(C.ACTIVE_GROUP_KEY)
        user_id = state.get(C.ACTIVE_USER_KEY)
        if current_group_id is not None and current_group_id != group_id:
            exit_group(user_id=user_id, group_id=current_group_id)
            change_group_event.set()
        elif current_group_id == group_id:
            display_manager.info(f"User {user_id} already in group {group_id}")
            return
        group_details = stub.GetGroup(
            chat_system_pb2.Group(group_id=group_id, user_id=user_id, session_id = state[C.SESSION_ID]))
        group_data = MessageToDict(group_details, preserving_proto_field_name=True)
        if group_details.status is True:
            display_manager.info(f"Successfully joined group {group_id}")
            display_manager.write_header(f"Group: {group_id}", f"Participants: {', '.join(set(group_data['users']))}")
            state[C.GROUP_DATA] = group_data
            state[C.MESSAGE_ID_TO_NUMBER_MAP] = {}
            state[C.TEXT_ID_TO_NUMBER_MAP] = {}
            state[C.MESSAGE_NUMBER] = 0
            state[C.TEXT_MSG_IDX] = 0
            state[C.MESSAGE_NUMBER_TO_ID_MAP] = {}
            state[C.MESSAGES] = {}
            state[C.MESSAGE_START_IDX] = -10
            state[C.ACTIVE_GROUP_KEY] = group_id
        else:
            raise Exception("Entering group not successful")
    except Exception as ex:
        display_manager.error(f"{ex}. Please try again.")
        raise ex


def get_timestamp() -> int:
    """
    returns UTC timestamp in microseconds
    """
    return int(datetime.now().timestamp() * 1_000_000)


def get_unique_id() -> str:
    """
    returns unique string generated by MD5 hash
    """
    return str(uuid.uuid4())


def build_message(message_text, message_number, message_type):
    
    if message_type == C.APPEND_TO_CHAT_COMMANDS[0]:
        message = chat_system_pb2.Message(
            group_id=state.get(C.ACTIVE_GROUP_KEY),
            user_id=state.get(C.ACTIVE_USER_KEY),
            creation_time=get_timestamp(),
            text=[message_text],
            message_id=state[C.MESSAGE_NUMBER_TO_ID_MAP][message_number],
            likes={},
            message_type=message_type
        )

    elif message_type == C.LIKE_COMMANDS[0]:
        message = chat_system_pb2.Message(
            group_id=state.get(C.ACTIVE_GROUP_KEY),
            user_id=state.get(C.ACTIVE_USER_KEY),
            creation_time=get_timestamp(),
            text=[],
            message_id=state[C.MESSAGE_NUMBER_TO_ID_MAP][message_number],
            likes={state[C.ACTIVE_USER_KEY]: 1},
            message_type=message_type
        )

    elif message_type == C.UNLIKE_COMMANDS[0]:
        message = chat_system_pb2.Message(
            group_id=state.get(C.ACTIVE_GROUP_KEY),
            user_id=state.get(C.ACTIVE_USER_KEY),
            creation_time=get_timestamp(),
            text=[],
            message_id=state[C.MESSAGE_NUMBER_TO_ID_MAP][message_number],
            likes={state[C.ACTIVE_USER_KEY]: 0},
            message_type=message_type
        )

    else:
        message_id=get_unique_id()

        message = chat_system_pb2.Message(
            group_id=state.get(C.ACTIVE_GROUP_KEY),
            user_id=state.get(C.ACTIVE_USER_KEY),
            creation_time=get_timestamp(),
            text=[message_text],
            message_id=message_id,
            likes={},
            message_type=C.NEW
        )
    return message


def post_message(message_text: str, post_message_queue: Queue, post_message_event: threading.Event, message_number, message_type):
    try:
        check_state(C.SENT_MESSAGE_CHECK)
        message = build_message(message_text, message_number, message_type)
        post_message_queue.put(message)
        post_message_event.set()
    except Exception as ex:
        raise ex


def send_messages(post_message_queue, post_message_event):
    while True:
        post_message_event.wait()  # sleeps till post_message_event.set() is called
        stub = state[C.STUB]
        while post_message_queue.qsize():
            message = post_message_queue.queue[0]
            retry = 3
            while retry > 0:
                try:
                    status = stub.PostMessage(message)
                    if status.status is True:
                        display_manager.debug("Message sent successfuly")
                        post_message_queue.get()

                    else:
                        logging.error(
                            f"Message sending failed. Response from server: {status.statusMessage}")
                    retry = 0
                    break
                except grpc.RpcError as rpcError:
                    retry -= 1
                    if retry == 0:
                        logging.error(
                            f"Message sending failed. Error: {rpcError}") 
            break
        post_message_event.clear()

def get_server_view():
    stub = state.get(C.STUB)
    if stub:
        server_status = stub.GetServerView(chat_system_pb2.BlankMessage())
        display_manager.info(f'Current Server View: {server_status.statusMessage}')
    pass

def run():
    
    status = None
    stub = None
    state[C.USER_JOINED_EVENT] = threading.Event()
    health_check_thread = Thread(target=health_check, daemon=True)
    health_check_thread.start()

    # retry queue that stores users' messages that will get delivered
    # even if message fails to be sent to server
    post_message_queue = Queue()
    post_message_event = threading.Event()
    send_message_thread = Thread(target=send_messages, args=[post_message_queue, post_message_event], daemon=True)
    send_message_thread.start()

    change_group_event = threading.Event()
    get_message_thread = Thread(target=get_messages, args=[change_group_event], daemon=True)
    get_message_thread.start()

    while True:
        
        user_input = display_manager.read()
        if ' ' in user_input:
            command = user_input.split(' ')[0].strip()
        else:
            command = user_input
        try:
            group_id = ''
            # connect mode : c
            if command in C.CONNECTION_COMMANDS:
                server_string = user_input[2:].strip()
                if server_string == '':
                    server_string = C.DEFAULT_SERVER_CONNECTION_STRING
                elif server_string in ['1', '2', '3', '4', '5']:
                    server_string = f'localhost:{11999+int(server_string)}'
                stub = join_server(server_string)

            # exit mode: q 
            elif command in C.EXIT_APP_COMMANDS:
                close_connection(channel=state.get(C.ACTIVE_CHANNEL))
                break

            # login user mode: u
            elif command in C.LOGIN_COMMANDS:
                user_id = user_input[2:].strip()
                if len(user_id) < 1:
                    raise Exception("Invalid user_id")
                get_user_connection(stub, user_id)

            # join group mode: j
            elif command in C.JOIN_GROUP_COMMANDS:
                group_id = user_input[2:].strip()
                if len(group_id) < 1:
                    raise Exception("Invalid group_id")
                enter_group_chat(stub, group_id, change_group_event)

            # join group mode: p
            elif command in C.PRINT_HISTORY_COMMANDS:
                state[C.MESSAGE_START_IDX] = 0
                state[C.MESSAGE_ID_TO_NUMBER_MAP] = {}
                state[C.TEXT_ID_TO_NUMBER_MAP] = {}
                state[C.MESSAGE_NUMBER] = 0
                state[C.TEXT_MSG_IDX] = 0
                state[C.MESSAGE_NUMBER_TO_ID_MAP] = {}
                state[C.MESSAGES] = {}
                change_group_event.set()
                display_manager.info('Chat History is printed successfully')
            
            # like mode: l
            elif command in C.LIKE_COMMANDS or command in C.UNLIKE_COMMANDS:
                splits = user_input.split(" ")
                message_number = splits[1]
                if not message_number.isdigit():
                    raise Exception("Invalid command")
                message_number = int(message_number)
                post_message(None, post_message_queue, post_message_event, message_number, message_type=command)
                display_manager.info('')

            # typing mode & also implement get messages mode
            elif command in C.APPEND_TO_CHAT_COMMANDS:
                splits = user_input.split(" ")
                message_number = splits[1]
                message_text = " ".join(splits[1:]).strip()
                post_message(message_text, post_message_queue, post_message_event, None, message_type=C.NEW)
                display_manager.info('')
            
            elif command in C.GET_SERVER_VIEW_COMMANDS:
                get_server_view()
                pass

            else:
                display_manager.error('Not a valid command!')
            
        except grpc.RpcError as rpcError:
            display_manager.error(f"grpc exception: {rpcError}")
        except Exception as e:
            display_manager.error(
                f"Error: {e}")


if __name__ == "__main__":
    
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%d-%m-%Y:%H:%M:%S',
                        level=logging.INFO)
    try:
        run()
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()
