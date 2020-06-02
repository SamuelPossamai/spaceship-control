
import time

from .objective import ObjectiveGroup

class TimedObjectiveGroup(ObjectiveGroup):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 time_limit: 'Union[int, float]',
                 name: str = 'Timed objectives list',
                 description: str = None,
                 **kwargs) -> None:

        if description is None:
            description = self._getDefaultDescription(
                subobjectives, name=name, description=description, **kwargs)
            description += f' in {time_limit} seconds'

        super().__init__(subobjectives, name=name, description=description,
                         **kwargs)

        self.__time_limit_val = time_limit
        self.__time_limit = time.time() + time_limit

    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:

        if time.time() > self.__time_limit:
            return False

        return super()._verify(space, ships)

    def _hasFailed(self, space: 'pymunk.Space',
                   ships: 'Sequence[Device]') -> bool:

        if time.time() > self.__time_limit:
            return True

        return super()._hasFailed(space, ships)

    def reset(self) -> None:
        self.__time_limit = time.time() + self.__time_limit
