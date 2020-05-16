"""Classes used to represent a goal.

This module contains classes that are used to represent the goals the
controllers need to complete.
"""

from abc import ABC, abstractmethod, abstractproperty

from anytree import Node

class Objective(ABC):
    """Base class for all objectives.

    This abstract class is the base for all classes that represent a scenario
    objective.

    """

    def __init__(self, name: str, description: str) -> None:
        super().__init__()

        self.__name = name
        self.__desc = description
        self.__acp = False

    def accomplished(self) -> bool:
        """Consult if the objective was accomplished.

        This method is used to know if the goal was accomplished, but it does
        not check if it is objective is complete now, so a call to 'verify'
        should be done before calling this method.

        Returns:
            True if it was accomplished otherwise False.

        """
        return self.__acp

    @property
    def description(self) -> str:
        """Returns the description of the objective.

        This method returns the description of this objective.

        Returns:
            A string containing the description of this objective.
        """
        return self.__desc

    @property
    def name(self) -> str:
        """Returns the name of the objective.

        This method returns the name of this objective.

        Returns:
            A string containing the name of this objective.
        """
        return self.__name

    def verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:
        """Verify if the objective is complete.

        If the objective was not accomplished before verify if it is now.

        Returns:
            True if it was accomplished otherwise False
        """

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
                 required_quantity: int = None,
                 sequential: bool = False) -> None:

        if sequential and required_quantity is not None:
            raise ValueError('ObjectiveGroup: It\'s not possible to specify'
                             ' required_quantity if it\'s sequential')

        if description is None:
            if required_quantity is not None:
                description = f'Complete {required_quantity} subobjectives'
            else:
                description = f'Complete all {len(subobjectives)} subobjectives'
                if sequential:
                    description += ' successively'

        super().__init__(name, description)

        self.__subobjectives = tuple(subobjectives)
        self.__req_qtd = required_quantity
        self.__seq = sequential

    @property
    def subobjectives(self):
        return self.__subobjectives

    def objectivesStatus(self) -> 'Sequence[Objective, bool]':

        return ((objective, objective.accomplished())
                for objective in  self.__subobjectives)

    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:

        if self.__seq:
            return all(objective.verify(space, ships)
                       for objective in self.__subobjectives)

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
