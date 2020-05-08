
from  pymunk import Vec2d

from .objective import Objective

class GoToObjective(Objective):

    def __init__(self, position, distance, name=None, description=None):
        if name is None:
            name = f'Go to position({position[0]}, {position[1]})'

        if description is None:
            description = ('Get the center of any ship near the position '
                           f'{position[0]}, {position[1]}, the maximum distance'
                           f' accepted is {distance}')

        super().__init__(name, description)

        self.__position = Vec2d(position)
        self.__distance = distance
        self.__distance_sqrtd = distance**2

    def _verifyShip(self, ship: 'Device') -> bool:
        pos = ship.body.position
        return pos.get_dist_sqrd(self.__position) < self.__distance_sqrtd

    def _verify(self, space: 'pymunk.Space', ships: 'Sequence[Device]') -> bool:
        del space

        return any(self._verifyShip(ship) for ship in ships)

    @property
    def info(self) -> 'Dict[str, Any]':
        return {
            'target-x': self.__position.x,
            'target-y': self.__position.y,
            'distance': self.__distance
        }
