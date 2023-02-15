
import logging
import curses
import client.constants as C

allowed_chat_chars = {}
for i in range(32, 127):
    allowed_chat_chars[i] = chr(i)
    
class DisplayManagerCurses():
    def __init__(self, stdscr) -> None:
        super().__init__()
        self.chars = []
        self.stdscr = stdscr
        self.stdscr.clear()
        self.stdscr.refresh()
        self.message_data = {}
        self.cursor_position = 0
        self.message_idx = 0
        self.group_name = ""
        self.participants = ""
        self.INPUT_PROMPT = C.INPUT_PROMPT + ": "
        self.scrollposition = 0
        self.resize()
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "")

    def render_messages(self):
        max_lines = self.message_end_line - 2
        if not self.message_data:
            return
        message_indices = sorted(list(self.message_data.keys()))
        total_lines = len(message_indices)
        start = max(0, total_lines - max_lines - self.scrollposition)
        end = total_lines - self.scrollposition
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
            if self.scrollposition > 0:
                self.scrollposition = 0
                self.info(C.NEW_MESSAGE_SCROLL)
            else:
                self.info("")

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
        if len(chars) > self.cursor_position:
            self.stdscr.addstr(self.input_line, 0, self.clear_line)
            chars.pop(self.cursor_position)
            self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars))
            self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(chars[:self.cursor_position]))
            self.stdscr.refresh()

    def backspace_chat_char(self, chars):
        if len(chars) > 0:
            self.stdscr.addstr(self.input_line, 0, self.clear_line)
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
    
    def scroll(self, c):
        max_lines = self.message_end_line - 2
        ## scroll up
        if c == 258:
            self.scrollposition -= 1
            if self.scrollposition < 0:
                self.info(C.SCROLL_REACHED_BOTTOM)
            else:
                self.info("")
            self.scrollposition = max(0, self.scrollposition)
        ## scroll down
        if c == 259:
            self.scrollposition += 1
            if self.scrollposition >= len(self.message_data)-max_lines:
                self.info(C.SCROLL_REACHED_TOP)
            else:
                self.info("")
            self.scrollposition = min(len(self.message_data)-max_lines, self.scrollposition)
        ## page down
        if c == 338:
            self.scrollposition -= max_lines
            if self.scrollposition < 0:
                self.info(C.SCROLL_REACHED_BOTTOM)
            else:
                self.info("")
            self.scrollposition = max(0, self.scrollposition)
        ## page up
        if c == 339:
            self.scrollposition += max_lines
            if self.scrollposition >= len(self.message_data)-max_lines:
                self.info(C.SCROLL_REACHED_TOP)
            else:
                self.info("")
            self.scrollposition = min(len(self.message_data)-max_lines, self.scrollposition)
        self.render_messages()

    def read(self, prompt=""):
        stdscr = self.stdscr
        chars = self.chars
        while True:
            c = stdscr.getch()
            if c in allowed_chat_chars:
                self.add_allowed_chat_chars(chars, c)
            elif c == 127 or c == curses.KEY_BACKSPACE:
                self.backspace_chat_char(chars)
            elif c == 330 or c == curses.KEY_DC:
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
                self.chars = []
                return s
            elif c == curses.KEY_RESIZE:
                self.resize()
            elif c in [258, 259, 339, 338]: ## Scroll up and down with mouse or arrow keys and also using page up and page down
                self.scroll(c)
            elif c == 262 or C == curses.KEY_HOME: ## Home button
                self.cursor_position = 0
                self.set_cursor_position()
            elif c == 360 or C == curses.KEY_END: ## End button
                self.cursor_position = len(chars)
                self.set_cursor_position()
            else:
                # print(c)
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
            self.stdscr.refresh()
            self.message_idx = 0
        else:
            self.render_header()

    def render_header(self):
        self.stdscr.addstr(0, 0, self.clear_line)
        self.stdscr.addstr(1, 0, self.clear_line)
        self.stdscr.addstr(0, 0, self.group_name[:self.x-1])

        if len(self.participants) > self.x - 1:
            self.participants = self.participants[:self.x-4] + "..." 

        self.stdscr.addstr(1, 0, self.participants)
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "")
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
        self.message_end_line = y - 4
        self.stdscr.clear()
        if self.group_name:
            self.render_header()
        self.render_messages()
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(self.chars))
        self.stdscr.addstr(self.input_line, 0, self.INPUT_PROMPT + "".join(self.chars[:self.cursor_position]))
        self.stdscr.refresh()

