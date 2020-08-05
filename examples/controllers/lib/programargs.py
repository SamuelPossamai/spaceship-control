
import sys
import json

from .goals import GoalList

class ProgramArgsInfo:

    def __init__(self):

        self.__json_content = json.loads(sys.argv[1])
        self.__starting_position = self.__json_content.get('starting-position')
        self.__starting_angle = self.__json_content.get('starting-angle')
        self.__ship_name = self.__json_content.get('ship-name')
        self.__goals = GoalList('GoalList', {
            'info': {
                'objectives': self.__json_content.get('objectives', ())
            }
        }, ship_name=self.__ship_name)

    @property
    def ship_name(self):
        return self.__ship_name

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
except Exception as err:
    print('programargs.py: An error occured:', err, file=sys.stderr)
    program_args_info = None
