
import shlex

class ConsoleInterface:

    def __init__(self, ship, input_stream, output_stream):

        self.__ship = ship
        self.__cur_ship = ship
        self.__istream = input_stream
        self.__ostream = output_stream
        self.__commands = self.__COMMANDS.copy()

    def run():

        result = None
        command = self.__istream.readline()
        if command:
            tokens = shlex.split(command, comments=True)

            cmd = tokens[0]
            cmd_args = tokens[1:]

            cmd_function = self.__commands.get(cmd)

            if cmd_function is None:
                result = 'Command \'{cmd}\' not found'
            else:
                try:
                    result = cmd_args(cmd, cmd_args)
                except Exception:
                    result = 'Error running command \'{cmd}\''

        self.__ostream.write(result)

    @staticmethod
    def __cmd_echo(cmd, cmd_args):
        self.__ostream.write(' '.join(cmd_args))

    @staticmethod
    def __cmd_echo(cmd, cmd_args):
        self.__ostream.write(' '.join(cmd_args))

    __COMMANDS = {
        'echo': __cmd_echo
    }
