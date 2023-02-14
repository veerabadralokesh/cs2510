
import logging
import curses
import client.constants as C

allowed_chat_chars = {}
for i in range(32, 127):
    allowed_chat_chars[i] = chr(i)
    
class DisplayManagerCurses():
    def __init__(self, stdscr) -> None:
        super().__init__()
        self.stdscr = stdscr
        self.stdscr.clear()
        self.stdscr.refresh()
        self.message_data = {}
        self.cursor_position = 0
        self.message_idx = 0
        self.group_name = ""
        self.participants = ""
        self.INPUT_PROMPT = C.INPUT_PROMPT + ": "
        self.resize()

    def render_messages(self):
        max_lines = self.message_end_line - 2
        if not self.message_data:
            return
        message_indices = sorted(list(self.message_data.keys()))
        total_lines = len(message_indices)
        start = max(0, total_lines - max_lines) 
        end = total_lines
        # if self.message_data:
            # print(self.message_data)
        for display_index, line_index in enumerate(message_indices[start:end]):
            self.stdscr.addstr(display_index + 3, 0, self.clear_line)
            self.stdscr.addstr(display_index + 3, 0, self.message_data[line_index])
        self.set_cursor_position()
        self.stdscr.refresh()

    def write(self, msg_indx, message):
        
        if self.group_name != "" and len(message) > 0:
            self.message_data[msg_indx] = message

        self.message_idx += 1
        self.render_messages()
    
    def display_info(self, display_string):
        if len(display_string) > self.x - 1:
            display_string = display_string[:self.x-4] + "..." 
        self.stdscr.addstr(self.y - 2, 0, self.clear_line)
        self.stdscr.addstr(self.y - 2, 0, display_string)
        self.set_cursor_position()
        self.stdscr.refresh()

    def error(self, error):
        if error is not None:
            error_string = f"Error: {error}"
            self.display_info(error_string)
            
    
    def info(self, info):
        if info is not None:
            info_string = f"{info}"
            self.display_info(info_string)
    
    def warn(self, *args):
        if len(args) > 0:
            # logging.warn(*args)
            pass
    
    def debug(self, *args):
        if len(args) > 0:
            # logging.debug(*args)
            pass
    
    def add_allowed_chat_chars(self, chars, c):
        ch = chr(c)
        chars.insert(self.cursor_position, ch)
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars))
        self.cursor_position += 1
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars[:self.cursor_position]))
        self.stdscr.refresh()

    def delete_chat_char(self, chars):
        if len(chars) > 0:
            self.stdscr.addstr(self.input_line, 0, " "*len(chars))
            chars.pop(self.cursor_position-1)
            self.cursor_position = max(0, self.cursor_position-1)
            #stdscr.clear()
            self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars))
            self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars[:self.cursor_position]))
            self.stdscr.refresh()

    def submit_input(self, chars):
        s = "".join(chars)
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + " " * min(len(chars), self.x-1))
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "")
        self.stdscr.refresh()
        self.cursor_position = 0
        return s

    def read(self, prompt=""):
        stdscr = self.stdscr
        chars = []
        while True:
            c = stdscr.getch()
            if c in allowed_chat_chars:
                self.add_allowed_chat_chars(chars, c)
            elif c == 127 or c == curses.KEY_BACKSPACE:
                self.delete_chat_char(chars)
            elif c == 260: # left arrow
                self.cursor_position = max(0, self.cursor_position-1)
                stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars[:self.cursor_position]))
                stdscr.refresh()
            elif c == 261: # right arrow
                self.cursor_position = min(len(chars), self.cursor_position+1)
                stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars[:self.cursor_position]))
                stdscr.refresh()
            elif c == ord('\n') or c == curses.KEY_ENTER:
                s =  self.submit_input(chars)
                chars = []
                return s
            elif c == curses.KEY_RESIZE:
                self.resize()
            else:
                pass
    
    def set_user(self, user_id):
        self.stdscr.addstr(self.input_line, 0, self.clear_line)
        self.INPUT_PROMPT = user_id + ": "
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "")
        self.stdscr.refresh()

    def write_header(self, group_name, participants):
        self.group_name = group_name
        self.participants = participants

        if group_name == "":
            self.message_data = {}
            self.stdscr.clear()
            self.message_idx = 0
            self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "")
            self.stdscr.refresh()
        else:
            self.render_header()

    def render_header(self):
        self.stdscr.addstr(0, 0, self.clear_line)
        self.stdscr.addstr(1, 0, self.clear_line)
        self.stdscr.addstr(0, 0, self.group_name[:self.x-1])

        if len(self.participants) > self.x - 1:
            self.participants = self.participants[:self.x-4] + "..." 

        self.stdscr.addstr(1, 0, self.participants)
        self.stdscr.refresh()
        self.set_cursor_position()
    
    def set_cursor_position(self):
        self.stdscr.addstr(self.input_line, len(self.INPUT_PROMPT) + self.cursor_position, "")
        self.stdscr.refresh()

    def clear(self):
        self.stdscr.clear()
        self.stdscr.refresh()
        self.message_data = {}
        self.cursor_position = 0
        self.message_idx = 0
        self.group_name = ""
        self.participants = ""
        self.resize()

    def resize(self):
        y, x = self.stdscr.getmaxyx()
        self.y = y
        self.x = x
        self.input_line = y-1
        self.clear_line = " " * (x-1)
        self.message_end_line = y - 3
        if self.group_name:
            self.render_header()
        self.render_messages()

