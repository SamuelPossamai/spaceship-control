
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
        output = ''.join(key.char for key in key_list if key.char is not None)
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
                        output += cmd_function(self, cmd, cmd_args)
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

    __COMMANDS = {
        'echo': __cmd_echo
    }
