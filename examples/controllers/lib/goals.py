
class Goal:

    def __init__(self, goals_info):

        self.__goal_info = goals_info
        self.__type = goals_info.get('type')
        self.__name = goals_info.get('name')
        self.__description = goals_info.get('description')
        self.__info = goals_info.get('info')

    def load(goals_info):
        return Goal(goals_info)

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
