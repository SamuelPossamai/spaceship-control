
import sys
import json

from .goals import Goal

class ProgramArgsInfo:

    def __init__(self):

        self.__json_content = json.loads(sys.argv[1])
        self.__starting_position = self.__json_content.get('starting-position')
        self.__starting_angle = self.__json_content.get('starting-angle')
        self.__goals = tuple(Goal.load(goal) for goal in
                             self.__json_content.get('objectives', ()))

    @property
    def starting_position(self):
        return self.__starting_position

    @property
    def starting_angle(self):
        return self.__starting_angle

    @property
    def goals(self):
        return self.__goals

    def __repr__(self):
        return (f'ProgramArgsInfo(starting_position={self.__starting_position})'
                f', starting_angle={self.__starting_angle}, goals='
                f'{self.__goals})')

try:
    program_args_info = ProgramArgsInfo()
except Exception:
    program_args_info = None
