
from abc import ABC, abstractmethod

class Objective(ABC):

    def __init__(self, name: str, description: str) -> None:
        super().__init__()

        self.__name = name
        self.__desc = description
        self.__acp = False

    def accomplished() -> bool:
        return self.__acp

    @property
    def description(self) -> str:
        return self.__desc

    @property
    def name(self) -> str:
        return self.__name

    def verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:

        if self.__acp is False:
            self.__acp = self._verify(space, ships)

        return self.__acp

    @abstractmethod
    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:
        pass

class ObjectiveGroup(ABC):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 name: str = 'Objectives list',
                 description: str = None) -> None:

        if description is None:
            description = f'Complete all {len(subobjectives)} subobjectives'

        super().__init__(name, description)

        self.__subobjectives = tuple(subobjectives)

    @property
    def subobjectives(self):
        return self.__subobjectives

    def objectivesStatus() -> 'Sequence[Objective, bool]':

        return ((objective, objective.accomplished())
                for objective in  self.__subobjectives)

    def accomplished(self) -> bool:
        return all(acp for _, acp in accomplishedList())

    def verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:
        return all(objective.verify() for objective in self.__subobjectives)