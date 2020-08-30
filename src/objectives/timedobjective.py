
import time
from typing import TYPE_CHECKING

from .objective import ObjectiveGroup

if TYPE_CHECKING:
    from typing import Sequence, Any
    import pymunk
    from .objective import Objective
    from ..devices.structure import Structure

class TimedObjectiveGroup(ObjectiveGroup):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 time_limit: float,
                 name: str = 'Timed objectives list',
                 description: str = None,
                 **kwargs: 'Any') -> None:

        if description is None:
            description = self._getDefaultDescription(
                subobjectives, name=name, description=description, **kwargs)
            description += f' in {time_limit} seconds'

        super().__init__(subobjectives, name=name, description=description,
                         **kwargs)

        self.__time_limit = time_limit

    def _verify(self, space: 'pymunk.Space',
                ships: 'Sequence[Structure]') -> bool:

        if time.time() > self.started_at + self.__time_limit:
            return False

        return super()._verify(space, ships)

    def _hasFailed(self, space: 'pymunk.Space',
                   ships: 'Sequence[Structure]') -> bool:

        if time.time() > self.started_at + self.__time_limit:
            return True

        return super()._hasFailed(space, ships)
