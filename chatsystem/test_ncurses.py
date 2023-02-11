#from curses import wrapper
from time import sleep
import curses
# from curses.textpad import Textbox, rectangle
from threading import Thread, Lock
import os


def main(stdscr):
    # Clear screen
    stdscr.clear()

    # pad1 = curses.newpad()
    lock = Lock()
    
    stdscr.refresh()

    allowed_chat_chars = {}
    for i in range(32, 127):
        allowed_chat_chars[i] = chr(i)
    
    

    line_data = {}
    global pad_line_number
    pad_line_number = 0
    cursor_position = 0
    chars = []
    y, x = stdscr.getmaxyx()
    line_number = y-1

    def add_text(s):
        global pad_line_number
        try:
            sleep(5)
            lock.acquire()
            stdscr.addstr(pad_line_number, 0, f"{pad_line_number}: echo: " + s)
            stdscr.addstr(line_number, cursor_position, "")
            stdscr.refresh()
            pad_line_number += 1
            lock.release()
        except:
            pass

    user_name = os.getenv('USER', 'You') + ": "
    stdscr.addstr(line_number, 0, "")
    while True:
        c = stdscr.getch()
        if c in allowed_chat_chars:
            ch = chr(c)
            chars.insert(cursor_position, ch)
            #stdscr.addstr(ch)
            stdscr.addstr(line_number, 0, "".join(chars))
            cursor_position += 1
            stdscr.addstr(line_number, 0, "".join(chars[:cursor_position]))
        elif c == 127:
            if len(chars) > 0:
                stdscr.addstr(line_number, 0, " "*len(chars))
                chars.pop(cursor_position-1)
                cursor_position = max(0, cursor_position-1)
                #stdscr.clear()
                stdscr.addstr(line_number, 0, "".join(chars))
                stdscr.addstr(line_number, 0, "".join(chars[:cursor_position]))
                stdscr.refresh()
        elif c == 260: # left arrow
            cursor_position = max(0, cursor_position-1)
            stdscr.addstr(line_number, 0, "".join(chars[:cursor_position]))
            stdscr.refresh()
        elif c == 261: # right arrow
            cursor_position = min(len(chars), cursor_position+1)
            stdscr.addstr(line_number, 0, "".join(chars[:cursor_position]))
            stdscr.refresh()
        elif c == ord('\n') or c == curses.KEY_ENTER:
            s = "".join(chars)
            if s.startswith("q"): break
            lock.acquire()
            line_data[pad_line_number] = s
            stdscr.addstr(pad_line_number, 0, f"{pad_line_number}: {user_name}" + s)
            stdscr.refresh()
            # stdscr.clear()
            stdscr.addstr(line_number, 0, " " * min(len(chars), x-1))
            stdscr.addstr(line_number, 0, "")
            stdscr.refresh()
            tread = Thread(target=add_text, args=[s], daemon=True)
            tread.start()
            chars = []
            cursor_position = 0
            pad_line_number += 1
            lock.release()
            # stdscr.addstr(line_number, 0, "")
        elif c == curses.KEY_RESIZE:
            y, x = stdscr.getmaxyx()
            line_number = y-1
            stdscr.clear()
            max_lines = y - 2
            total_lines = len(line_data)
            start = max(0, total_lines-max_lines)
            end = total_lines
            for display_index, line_index in enumerate(range(start, end)):
                stdscr.addstr(display_index, 0, f"{line_index}: {user_name}" + line_data[line_index])
            stdscr.addstr(line_number, 0, "".join(chars))
            stdscr.addstr(line_number, 0, "".join(chars[:cursor_position]))
            stdscr.refresh()
        else:
            pass
            # try:
            #     stdscr.clear()
            #     stdscr.addstr(line_number, 0, ";" + str(30+c) + "," + str(c) + ";")
            #     stdscr.refresh()
            # except:
            #     pass

curses.wrapper(main)
