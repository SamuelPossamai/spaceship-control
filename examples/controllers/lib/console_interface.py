
import shlex
from .spctrl_base_controller import (
    SimpleConsoleOutputDevice, TranslatedKeyboardInputDevice
)

class ConsoleInterface:

    def __init__(self, ship, input_stream, output_stream):

        self.__ship = ship
        self.__cur_ship = ship
        self.__istream = TranslatedKeyboardInputDevice(input_stream)
        self.__ostream = SimpleConsoleOutputDevice(output_stream)
        self.__commands = self.__COMMANDS.copy()
        self.__cur_command = ''

        self.__ostream.write('> ')
        self.__ostream.flush()

    def run(self):

        key_list = self.__istream.readline()

        input_chars = []
        for key in key_list:
            if key.control:
                if key.char == 'l' or key.char == 'L':
                    self.__ostream.clear()
                    self.__ostream.write('> ')
                    self.__ostream.flush()
                elif key.char == 'u' or key.char == 'U':
                    self.__ostream.sendMessage('set-cursor-pos-x 2')
                    self.__ostream.write(' '*len(self.__cur_command))
                    self.__ostream.flush()
                    self.__ostream.sendMessage('set-cursor-pos-x 2')
                    self.__cur_command = ''

            elif key.char is not None:
                input_chars.append(key.char)

        output = ''.join(input_chars)
        self.__cur_command += output

        if self.__cur_command and self.__cur_command[-1] == '\n':
            tokens = shlex.split(self.__cur_command[:-1], comments=True)

            if tokens:

                cmd = tokens[0]
                cmd_args = tokens[1:]

                cmd_function = self.__commands.get(cmd)

                if cmd_function is None:
                    output += f'Command \'{cmd}\' not found'
                else:
                    try:
                        output += str(cmd_function(self, cmd, cmd_args))
                    except Exception:
                        raise
                        output += f'Error running command \'{cmd}\''

                output += '\n'

            output += '> '
            self.__cur_command = ''

        if output:
            self.__ostream.write(output)
            self.__ostream.flush()

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

    __COMMANDS = {
        'echo': __cmd_echo,
        'show-position': __cmd_show_position,
        'show-angle': __cmd_show_angle,
        'show-speed': __cmd_show_speed,
        'show-angular-speed': __cmd_show_angular_speed
    }
