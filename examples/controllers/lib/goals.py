
class Goal:

    _GOAL_TYPE_MAP = {}

    def __init__(self, type_, goal_info, ship_name=None):

        self.__goal_info = goal_info
        self.__type = type_
        self.__name = goal_info.get('name')
        self.__description = goal_info.get('description')
        self.__info = goal_info.get('info')
        self.__negation = goal_info.get('negation', False)
        self.__required = goal_info.get('required', True)
        self.__valid_ships = goal_info.get('ships')

        if ship_name is None or self.__valid_ships is None:
            self.__valid = True
        else:
            self.__valid = ship_name in self.__valid_ships

    def load(goal_info, ship_name=None):

        type_ = goal_info.get('type')

        return Goal._GOAL_TYPE_MAP.get(type_, Goal)(
            type_, goal_info, ship_name=ship_name)

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

    @property
    def negation(self):
        return self.__negation

    @property
    def required(self):
        return self.__required

    @property
    def valid(self):
        return self.__valid

    def __repr__(self):
        return f'Goal: {self.__name}'

class GoalList(Goal):

    def __init__(self, type_, goal_info, ship_name=None):
        super().__init__(type_, goal_info, ship_name=ship_name)

        self.__goals = tuple(Goal.load(goal_info, ship_name=ship_name)
                             for goal_info in self.info.get('objectives', ()))

    def goals(self):
        return self.__goals

    def __getitem__(self, val):
        return self.__goals[val]

    def __iter__(self):
        return iter(self.__goals)

    def __contains__(self, value):
        return value in self.__goals

    def __len__(self):
        return len(self.__goals)

    def __format__(self, format_spec):
        return format(self.__goals, format_spec)

    def __str__(self):
        return str(self.__goals)

    def __repr__(self):
        return repr(self.__goals)

Goal._GOAL_TYPE_MAP['ObjectiveGroup'] = GoalList

class GoToGoal(Goal):

    def __init__(self, type_, goal_info, ship_name=None):
        super().__init__(type_, goal_info, ship_name=ship_name)

        info = self.info

        self.__pos = info.get('target-x'), info.get('target-y')
        self.__distance = info.get('distance')

    @property
    def pos(self):
        return self.__pos

    @property
    def distance(self):
        return self.__distance


Goal._GOAL_TYPE_MAP['GoToObjective'] = GoToGoal
