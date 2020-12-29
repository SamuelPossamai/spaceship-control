
import shlex

from PyQt5.QtCore import Qt

from .spctrl_base_controller import (
    SimpleConsoleOutputDevice as SCOD, TranslatedKeyboardInputDevice as TKID
)

class ConsoleInterface:

    def __init__(self, ship, input_stream, output_stream):

        self.__ship = ship
        self.__cur_ship = ship
        self.__istream = TKID(input_stream)
        self.__ostream = SCOD(output_stream)
        self.__commands = self.__COMMANDS.copy()
        self.__cur_command = ''
        self.__editing_command = ''
        self.__cur_start_console_line = 0
        self.__history = []
        self.__cur_cmd_history_index = None
        self.__cur_column_offset = 0
        self.__cur_device = ship.device
        self.__console_size = (int(self.__ostream.sendMessage('get-columns')),
                               int(self.__ostream.sendMessage('get-rows')))

        self.__ostream.sendMessage('show-cursor')
        self.__ostream.write('> ')
        self.__ostream.flush()

    def run(self):

        key_list = self.__istream.readline()

        input_chars = []
        enter_pressed = False
        for key in key_list:
            if key.char == '\n':
                enter_pressed = True
            elif key.code == Qt.Key_Backspace:
                if self.__cur_command:
                    self.__ostream.sendMessage('BS')
                    if self.__cur_column_offset == 0:
                        self.__ostream.write(' ', mode=SCOD.WriteMode.Static)
                        self.__ostream.flush()
                        self.__cur_command = self.__cur_command[:-1]
                    else:
                        cur_column = -self.__cur_column_offset - 1
                        cur_cmd_after = self.__cur_command[cur_column + 1:]
                        self.__ostream.write(cur_cmd_after + ' ',
                                             mode=SCOD.WriteMode.Static)
                        self.__ostream.flush()
                        self.__cur_command = self.__cur_command[:cur_column] + \
                            cur_cmd_after
            elif key.code == Qt.Key_Home:
                self.__cur_column_offset = len(self.__cur_command) - 1
                self.__ostream.sendMessage(
                    f'set-cursor-pos 2 {self.__cur_start_console_line}')
            elif key.code == Qt.Key_End:
                self.__cur_column_offset = 0
                self.__replace_string(self.__cur_command)
            elif key.code == Qt.Key_Up:
                if self.__cur_cmd_history_index is None:
                    self.__cur_cmd_history_index = len(self.__history) - 1
                    self.__editing_command = self.__cur_command
                else:
                    self.__cur_cmd_history_index -= 1

                if self.__cur_cmd_history_index >= 0:
                    self.__replace_string(
                        self.__history[self.__cur_cmd_history_index])
                else:
                    self.__cur_cmd_history_index = 0
            elif key.code == Qt.Key_Left:
                if self.__cur_column_offset < len(self.__cur_command):
                    self.__cur_column_offset += 1
                    self.__ostream.sendMessage('BS')
            elif key.code == Qt.Key_Right:
                if self.__cur_column_offset > 0:
                    self.__cur_column_offset -= 1
                    self.__ostream.sendMessage('advance-cursor')
            elif key.code == Qt.Key_Down:
                if self.__cur_cmd_history_index is not None:
                    self.__cur_cmd_history_index += 1

                    if self.__cur_cmd_history_index < len(self.__history):
                        self.__cur_command = self.__history[
                            self.__cur_cmd_history_index]
                        self.__replace_string(self.__cur_command)
                    else:
                        self.__replace_string(self.__editing_command)
                        self.__cur_cmd_history_index = None
            elif key.control:
                if key.char == 'l' or key.char == 'L':
                    self.__ostream.clear()
                    self.__ostream.write('> ')
                    self.__ostream.flush()
                elif key.char == 'u' or key.char == 'U':
                    self.__replace_string('')
                elif key.char == 'k' or key.char == 'K':
                    if self.__cur_column_offset != 0:
                        self.__replace_string(
                            self.__cur_command[:-self.__cur_column_offset])
                        self.__cur_column_offset = 0
            elif key.char is not None:
                input_chars.append(key.char)

        output = ''.join(input_chars)
        if output:
            if self.__cur_column_offset == 0:
                self.__cur_command += output
            else:
                index_pos = \
                    len(self.__cur_command) - self.__cur_column_offset
                self.__cur_command = self.__cur_command[:index_pos] + output + \
                    self.__cur_command[index_pos:]

        new_line = False
        if enter_pressed:
            output += '\n'

            tokens = shlex.split(self.__cur_command, comments=True)

            if tokens:
                self.__history.append(self.__cur_command)
                self.__cur_cmd_history_index = None

                cmd = tokens[0]
                cmd_args = tokens[1:]

                cmd_function = self.__commands.get(cmd)

                if cmd_function is None:
                    output += f'Command \'{cmd}\' not found'
                else:
                    try:
                        output += str(cmd_function(self, cmd, cmd_args))
                    except Exception:
                        output += f'Error running command \'{cmd}\''

                output += '\n'
                self.__cur_column_offset = 0

            new_line = True
            output += '> '
            self.__cur_command = ''

        if output:
            columns = self.__console_size[0]
            rows = self.__console_size[1]
            remaining_chars = rows*columns - \
                (self.__cur_start_console_line + 1)*columns - 2

            output_size = output.count('\n')*columns + len(output) - \
                output.rfind('\n')
            if output_size > remaining_chars:
                rows_to_push = (output_size - remaining_chars)//columns + 1
                if rows_to_push < rows:
                    rows_to_push = rows
                    self.__ostream.sendMessage('clear')
                    output = '\n'.join(output.rsplit('\n', rows - 1)[1:])
                else:
                    for i in range(rows_to_push):
                        self.__ostream.sendMessage('push-up')

            self.__ostream.write(output, mode=SCOD.WriteMode.Push)
            self.__ostream.flush()

        if new_line is True:
            try:
                self.__cur_start_console_line = int(
                    self.__ostream.sendMessage('get-cursor-pos-y'))
            except ValueError:
                pass

    def __replace_string(self, new_string):
        set_pos_command = f'set-cursor-pos 2 {self.__cur_start_console_line}'
        self.__ostream.sendMessage(set_pos_command)
        self.__ostream.write(' '*len(self.__cur_command),
                             mode=SCOD.WriteMode.Static)
        self.__ostream.write(new_string)
        self.__ostream.flush()
        self.__cur_command = new_string

    def __cmd_echo(self, cmd, cmd_args):
        return ' '.join(cmd_args)

    def __cmd_show_position(self, cmd, cmd_args):
        return self.__ship.position

    def __cmd_show_angle(self, cmd, cmd_args):
        return self.__ship.angle

    def __cmd_show_speed(self, cmd, cmd_args):
        return self.__ship.speed

    def __cmd_show_angular_speed(self, cmd, cmd_args):
        return self.__ship.angular_speed

    def __list_device(self, cmd, cmd_args):
        return str(self.__cur_device)

    def __use_device(self, cmd, cmd_args):

        if len(cmd_args) < 1:
            return 'Missing positional argument \'device\''

        child_id = cmd_args[0]
        children = self.__cur_device.children

        try:
            child_id = int(child_id)
            if child_id < len(children):
                self.__cur_device = children[child_id]
                return 'Device changed'

            return 'Device not found'

        except ValueError:
            pass

        for child_device in children:
            if child_device.name == child_id:
                self.__cur_device = child_device
                return 'Device changed'

        return 'Device not found'

    __COMMANDS = {
        'echo': __cmd_echo,
        'show-position': __cmd_show_position,
        'show-angle': __cmd_show_angle,
        'show-speed': __cmd_show_speed,
        'show-angular-speed': __cmd_show_angular_speed,
        'device': __list_device,
        'use': __use_device,
    }
