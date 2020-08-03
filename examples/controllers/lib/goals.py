
class Goal:

    _GOAL_TYPE_MAP = {}

    def __init__(self, goal_info):

        self.__goal_info = goal_info
        self.__type = goal_info.get('type')
        self.__name = goal_info.get('name')
        self.__description = goal_info.get('description')
        self.__info = goal_info.get('info')

    def load(goal_info):
        return Goal(goal_info)

    @property
    def type_(self):
        return self.__type

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def info(self):
        return self.__info

    def __repr__(self):
        return f'Goal: {self.__name}'

class GoToGoal(Goal):

    def __init__(self, goal_info):
        super().__init__(goal_info)

        info = self.info

        self.__pos = info.get('x-position'), info.get('y-position')
        self.__distance = info.get('distance')

    @property
    def pos(self):
        return self.__pos

    @property
    def distance(self):
        return self.__distance

Goal._GOAL_TYPE_MAP['GoToObjective'] = GoToGoal
