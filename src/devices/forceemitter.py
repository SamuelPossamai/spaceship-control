
from pymunk import Vec2d, ShapeFilter

from ..utils.interval import Interval, IntervalSet

from .structure import Actuator

class ForceEmitter(Actuator):

    def __init__(self, part: 'StructuralPart',
                 device_type: str = 'force-emitter',
                 **kwargs: 'Any') -> None:
        super().__init__(part, device_type=device_type,
                         properties={
                             'intensity': ForceEmitter.intensity,
                             'angle': ForceEmitter.angle
                         })

        min_intensity: float = kwargs.get('min_intensity', 0)
        max_intensity: float = kwargs.get('min_intensity', min_intensity + 1)

        min_angle: float = kwargs.get('max_angle', 0)
        max_angle: float = kwargs.get('min_angle', min_angle)

        self.__thrust: float = kwargs.get('start_intensity', min_intensity)
        self.__angle: float = kwargs.get('start_angle', min_intensity)

        self.__valid_intensities = IntervalSet(
            (Interval(min_intensity, max_intensity),))
        self.__valid_angles = IntervalSet((Interval(min_angle, max_angle),))

    @property
    def intensity(self) -> float:
        return self.__thrust

    @intensity.setter
    def intensity(self, val: 'Union[str, float]') -> None:

        if isinstance(val, str):
            val = float(val)

        if self.__valid_intensities is None or \
            self.__valid_intensities.isInside(val):

            self.__thrust = val

    @property
    def angle(self) -> float:
        return self.__angle

    @angle.setter
    def angle(self, val: 'Union[str, float]') -> None:

        if isinstance(val, str):
            val = float(val)

        if self.__valid_angles is None or \
            self.__valid_angles.isInside(val):

            self.__angle = val

    def actuate(self) -> None:

        structure = self.structural_part.structure

        if structure is None:
            return

        space = structure.space
        body = structure.body

        pos = self.structural_part.position
        segment_end = Vec2d(1000, 0)
        segment_end.angle = self.structural_part.angle + self.__angle

        collisions = space.segment_query(pos, pos + segment_end, 10,
                                         ShapeFilter())

        first_collision = next((col for col in collisions
                                if col.shape.body is not body), None)

        if first_collision is None:
            return

        force = Vec2d(-self.__thrust, 0)
        force.angle = self.structural_part.angle

        first_collision.shape.body.apply_force_at_world_point(
            force, first_collision.point)

        body.apply_force_at_world_point(-force, pos)
