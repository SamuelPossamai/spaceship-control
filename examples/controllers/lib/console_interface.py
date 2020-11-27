
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

    def run(self):

        key_list = self.__istream.read()
        command = ''.join(key.char for key in key_list if key.char is not None)
        output = command

        if False and command:
            tokens = shlex.split(command, comments=True)

            cmd = tokens[0]
            cmd_args = tokens[1:]

            cmd_function = self.__commands.get(cmd)

            if cmd_function is None:
                output += f'Command \'{cmd}\' not found'
            else:
                try:
                    output += cmd_args(cmd, cmd_args)
                except Exception:
                    output += f'Error running command \'{cmd}\''

        if output:
            self.__ostream.write(output)
            self.__ostream.flush()

    @staticmethod
    def __cmd_echo(cmd, cmd_args):
        return ' '.join(cmd_args)

    __COMMANDS = {
        'echo': __cmd_echo
    }
