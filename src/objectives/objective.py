"""Classes used to represent a goal.

This module contains classes that are used to represent the goals the
controllers need to complete.
"""

from abc import ABC, abstractmethod, abstractproperty
import time
from typing import TYPE_CHECKING

from anytree import Node

if TYPE_CHECKING:
    from typing import (
        Sequence, Optional, Dict, Any, Union, Iterable, Tuple, Collection
    )
    import pymunk
    from ..devices.structure import Structure

class Objective(ABC):
    """Base class for all objectives.

    This abstract class is the base for all classes that represent a scenario
    objective.

    """

    def __init__(self, name: str, description: str,
                 required: bool = None, negation: bool = False,
                 valid_ships: 'Collection[str]' = None) -> None:
        super().__init__()

        self.__name = name
        self.__desc = description
        self.__acp = False
        self.__failed = False
        self.__neg = negation
        self.__start = time.time()
        self.__finish: 'Optional[float]' = None
        if valid_ships is None:
            self.__valid_ships = None
        else:
            self.__valid_ships = set(valid_ships)

        if required is None:
            self.__required = not negation

    def failed(self) -> bool:

        if self.__neg is True:
            return self.__acp

        return self.__failed

    @property
    def valid_ships(self) -> 'Optional[Collection[str]]':
        return self.__valid_ships

    @property
    def started_at(self) -> 'float':
        return self.__start

    @property
    def finished_at(self) -> 'Optional[float]':
        return self.__finish

    def accomplished(self) -> bool:
        """Consult if the objective was accomplished.

        This method is used to know if the goal was accomplished, but it does
        not check if it is objective is complete now, so a call to 'verify'
        should be done before calling this method.

        Returns:
            True if it was accomplished otherwise False.

        """

        if self.__required is False:
            return not self.failed()

        if self.__neg is True:
            return self.__failed

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

    def verify(self, space: 'pymunk.Space',
               ships: 'Sequence[Structure]') -> bool:
        """Verify if the objective is complete or if it was failed.

        Returns:
            True if it was accomplished otherwise False
        """

        if self.__valid_ships is not None:
            ships = tuple(
                ship for ship in ships if ship.name in self.__valid_ships)

        if self.__acp is False and self.__failed is False:
            if self._verify(space, ships) is True:
                self.__acp = True
                self.__finish = time.time()
            elif self._hasFailed(space, ships):
                self.__failed = True
                self.__finish = time.time()

        return self.accomplished()

    @abstractmethod
    def _verify(self, space: 'pymunk.Space',
                ships: 'Sequence[Structure]') -> bool:
        pass

    @staticmethod
    def _hasFailed(space: 'pymunk.Space',
                   ships: 'Sequence[Structure]') -> bool:
        del space
        del ships
        return False

    def toDict(self) -> 'Dict[str, Any]':
        return {
            'type': self.__class__.__name__,
            'name': self.name,
            'description': self.description,
            'info': self.info,
            'negation': self.__neg,
            'required': self.__required,
            'ships': self.__valid_ships
        }

    @abstractproperty
    def info(self) -> 'Dict[str, Any]':
        pass

    def reset(self) -> None:
        self.__acp = False
        self.__failed = False
        self.__start = time.time()
        self.__finish = None

class ObjectiveGroup(Objective):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 name: str = 'Objectives list',
                 description: str = None,
                 required_quantity: int = None,
                 sequential: bool = False,
                 times: int = 1,
                 **kwargs: 'Any') -> None:

        if sequential and required_quantity is not None:
            raise ValueError('ObjectiveGroup: It\'s not possible to specify'
                             ' required_quantity if it\'s sequential')

        if description is None:
            description = self._getDefaultDescription(
                subobjectives, name=name, description=description,
                required_quantity=required_quantity, sequential=sequential)

        super().__init__(name, description, **kwargs)

        self.__subobjectives = tuple(subobjectives)
        self.__req_qtd = required_quantity
        self.__seq = sequential
        self.__times = times
        self.__times_left = times

    @property
    def subobjectives(self) -> 'Sequence[Objective]':
        return self.__subobjectives

    def objectivesStatus(self) -> 'Iterable[Tuple[Objective, bool]]':

        return ((objective, objective.accomplished())
                for objective in  self.__subobjectives)

    def __verifyInteral(self, space: 'pymunk.Space',
                        ships: 'Sequence[Structure]') -> bool:

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

    def _verify(self, space: 'pymunk.Space',
                ships: 'Sequence[Structure]') -> bool:

        if self.__verifyInteral(space, ships) is True:
            self.__times_left -= 1

        if self.__times_left <= 0:
            return True

        return False

    def _hasFailed(self, space: 'pymunk.Space',
                   ships: 'Sequence[Structure]') -> bool:

        failed_gen = (objective.failed() for objective in self.__subobjectives)

        if self.__req_qtd is None:
            return any(failed_gen)

        return sum(failed_gen) > (len(self.__subobjectives) - self.__req_qtd)

    @property
    def info(self) -> 'Dict[str, Any]':
        return {
            'objectives':
                [objective.toDict() for objective in self.__subobjectives]
        }

    @staticmethod
    def _getDefaultDescription(subobjectives: 'Sequence[Objective]',
                               **kwargs: 'Any') -> str:

        required_quantity = kwargs.get('required_quantity')
        if required_quantity is not None:
            return f'Complete {required_quantity} subobjectives'

        description = f'Complete all {len(subobjectives)} subobjectives'
        if kwargs.get('sequential'):
            description += ' successively'

        return description

    def reset(self) -> None:
        super().reset()

        self.__times_left = self.__times

def createObjectiveTree(objective: 'Union[Objective, Sequence[Objective]]',
                        parent: 'Node' = None) -> 'Node':

    if not isinstance(objective, Objective):
        node = Node(None)
        for obj in objective:
            createObjectiveTree(obj, parent=node)

        return node

    current_node = Node(objective, parent=parent)

    if isinstance(objective, ObjectiveGroup):

        for subobjective in objective.subobjectives:
            createObjectiveTree(subobjective, parent=current_node)

    return current_node
