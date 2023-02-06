
from __future__ import print_function

import logging
import grpc
import chat_system_pb2
import chat_system_pb2_grpc

from google.protobuf.json_format import MessageToJson

from client import client_constants
from client.display_manager import display_manager

global state

state = {

}

def check_state(check_point):
    if check_point > client_constants.SERVER_CONNECTION:
        if not state.get('server_connection_active'):
            raise Exception(client_constants.NO_ACTIVE_SERVER)
    if check_point > client_constants.USER_LOGIN:
        if state.get('active_user_id') is None:
            raise Exception(client_constants.NO_ACTIVE_USER)
    # if check_point == client_constants.JOIN_GROUP:

def manage_exits(stub=None, channel=None, user_id=None, group_id=None):
    if channel is not None:
        if state.get('active_user_id') is not None:
            manage_exits(stub=state.get('stub'), user_id=user_id)
        state['channel'] = None
        state['server_connection_active'] = False
        state['server_string'] = None
        state['stub'] = None
        channel.close()
        display_manager.info(f"terminated {state['server_string']} successfully")
    if user_id is not None and group_id is None:
        if state.get('active_user_id') is not None and state.get('active_user_id')==user_id:
            if state.get('active_group_id') is not None:
                manage_exits(stub, user_id=user_id, group_id=state['active_group_id'])
            stub.LogoutUser(chat_system_pb2.User(user_id=user_id))
            display_manager.info(f"Logout successful for user_id {user_id}")
            state['active_user_id'] = None
    if user_id is not None and group_id is not None:
        if state.get('active_user_id') is not None and state.get('active_user_id')==user_id \
            and state.get('active_group_id') is not None and state.get('active_group_id')==group_id:
            stub.ExitGroup(chat_system_pb2.Group(group_id=group_id, user_id=user_id))
            display_manager.info(f"{user_id} successfully exited group {group_id}")
            state['active_group_id'] = None


def join_server(server_string):
    if server_string == state.get('server_string'):
        display_manager.info(f'Already connected to server {server_string}')
        return state.get('stub')
    channel = state.get('channel')
    manage_exits(channel)
    channel = grpc.insecure_channel(server_string)
    stub = chat_system_pb2_grpc.ChatServerStub(channel)
    server_status = stub.HealthCheck(chat_system_pb2.BlankMessage())
    if server_status.status is True:
        display_manager.info("Server connection active")
        state['channel'] = channel
        state['server_connection_active'] = True
        state['server_string'] = server_string
        state['stub'] = stub
    return stub

def get_user_connection(stub, user_id):
    try:
        check_state(client_constants.USER_LOGIN)
        if state.get('active_user_id') is not None:
            if state.get('active_user_id') != user_id:
                manage_exits(stub, user_id=state['active_user_id'])
            else:
                display_manager.info(f"User {user_id} already logged in")
                return
        status = stub.GetUser(chat_system_pb2.User(user_id=user_id))
        if status.status is True:
            display_manager.info(f"Login successful with user_id {user_id}")
            state['active_user_id'] = user_id
        else:
            raise Exception("Login not successful")
    except grpc.RpcError as rpcError:
        raise rpcError
    except Exception as ex:
        raise ex

def enter_group_chat(stub, group_id):
    try:
        check_state(client_constants.JOIN_GROUP)
        current_group_id = state.get('active_group_id')
        user_id = state.get('active_user_id')
        if current_group_id is not None and current_group_id != group_id:
            manage_exits(stub, user_id=user_id, group_id=current_group_id)
        elif current_group_id == group_id:
            display_manager.info(f"User {user_id} already in group {group_id}")
            return
        group_details = stub.GetGroup(chat_system_pb2.Group(group_id=group_id, user_id=user_id))
        group_data = MessageToJson(group_details)
        if group_details.status is True:
            display_manager.info(f"Successfully joined group {group_id}")
            state['active_group_id'] = group_id
            state['group_data'] = group_data
        else:
            raise Exception("Entering group not successful")
    except Exception as ex:
        # print(f"Error: {ex}. Please try again.")
        raise ex


def chat(stub):

    return client_constants.EXIT_CODE


def run():
    status = None
    stub = None
    while True:
        # display_manager.write("hello", "world")
        command = display_manager.read()
        try:
            if command.startswith('c '):
                server_string = command[2:].strip()
                if server_string == '':
                    server_string = 'localhost:12000'
                stub = join_server(server_string)
            elif command.startswith('u '):
                user_id = command[2:].strip()
                get_user_connection(stub, user_id)
            elif command.startswith('j '):
                group_id = command[2:].strip()
                enter_group_chat(stub, group_id)
            else:
                display_manager.warn("Unkown command")
        except grpc.RpcError as rpcError:
            display_manager.error(f"grpc exception: {rpcError}")
        except Exception as e:
            display_manager.error(f"Error processing the request, please try again. {e}")
        if status == client_constants.EXIT_CODE:
            break

if __name__ == "__main__":

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    run()
