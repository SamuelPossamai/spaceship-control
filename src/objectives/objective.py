
from abc import ABC, abstractmethod, abstractproperty

from anytree import Node

class Objective(ABC):

    def __init__(self, name: str, description: str) -> None:
        super().__init__()

        self.__name = name
        self.__desc = description
        self.__acp = False

    def accomplished(self) -> bool:
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

    def toDict(self) -> 'Dict[str, Any]':
        return {
            'type': self.__class__.__name__,
            'name': self.name,
            'description': self.description,
            'info': self.info
        }

    @abstractproperty
    def info(self) -> 'Dict[str, Any]':
        pass

class ObjectiveGroup(Objective):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 name: str = 'Objectives list',
                 description: str = None,
                 required_quantity: int = None) -> None:

        if description is None:
            description = f'Complete all {len(subobjectives)} subobjectives'

        super().__init__(name, description)

        self.__subobjectives = tuple(subobjectives)
        self.__req_qtd = required_quantity

    @property
    def subobjectives(self):
        return self.__subobjectives

    def objectivesStatus(self) -> 'Sequence[Objective, bool]':

        return ((objective, objective.accomplished())
                for objective in  self.__subobjectives)

    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:

        for objective in self.__subobjectives:
            objective.verify(space, ships)

        acc_gen = (objective.accomplished()
                   for objective in self.__subobjectives)

        if self.__req_qtd is None:
            return all(acc_gen)

        return sum(acc_gen) >= self.__req_qtd

    @property
    def info(self) -> 'Dict[str, Any]':
        return {
            'objectives':
                [objective.toDict() for objective in self.__subobjectives]
        }

def createObjectiveTree(objective: 'Union[Objective, Sequence[Objective]]',
                        parent: 'Node' = None) -> 'Node':

    current_node = Node(objective, parent=parent)

    if isinstance(objective, ObjectiveGroup):

        for subobjective in objective.subobjectives:
            createObjectiveTree(subobjective, parent=current_node)
