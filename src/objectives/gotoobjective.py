
from typing import TYPE_CHECKING, cast as typingcast

from  pymunk import Vec2d

from .objective import Objective

if TYPE_CHECKING:
    from typing import Any, Dict, Sequence, Tuple
    import pymunk
    from ..devices.structure import Structure

class GoToObjective(Objective):

    def __init__(self, position: 'Tuple[float, float]', distance: float,
                 name: str = None, description: str = None,
                 **kwargs: 'Any') -> None:
        if name is None:
            name = f'Go to position({position[0]}, {position[1]})'

        if description is None:
            description = ('Get the center of any ship near the position '
                           f'{position[0]}, {position[1]}, the maximum distance'
                           f' accepted is {distance}')

        super().__init__(name, description, **kwargs)

        self.__position = Vec2d(position)
        self.__distance = distance
        self.__distance_sqrtd = distance**2

    def _verifyShip(self, ship: 'Structure') -> bool:
        pos = ship.body.position
        return typingcast(
            bool,
            pos.get_dist_sqrd(self.__position) < self.__distance_sqrtd)

    def _verify(self, space: 'pymunk.Space',
                ships: 'Sequence[Structure]') -> bool:
        del space

        return any(self._verifyShip(ship) for ship in ships)

    @property
    def info(self) -> 'Dict[str, Any]':
        return {
            'target-x': self.__position.x,
            'target-y': self.__position.y,
            'distance': self.__distance
        }
