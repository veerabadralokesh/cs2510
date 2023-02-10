from datetime import datetime


def get_timestamp() -> int:
    """
    returns UTC timestamp in microseconds
    """
    return int(datetime.now().timestamp() * 1_000_000)



def is_valid_message(message):
    
    return True