
import time

from .objective import ObjectiveGroup

class TimedObjectiveGroup(ObjectiveGroup):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 time_limit: 'Union[int, float]',
                 name: str = 'Timed objectives list',
                 description: str = None) -> None:

        if description is None:
            description = (f'Complete all {len(subobjectives)} subobjectives'
                           f' in {time_limit} seconds')

        super().__init__(subobjectives, name=name, description=description)

        self.__start_time = time.time()
        self.__time_limit = time_limit

    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:

        if time.time() - self.__start_time > self.__time_limit:
            return False

        return super()._verify(space, ships)
