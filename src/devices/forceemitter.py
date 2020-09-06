
from pymunk import Vec2d, ShapeFilter

from .structure import Actuator

class ForceEmitter(Actuator):

    def __init__(self, part: 'StructuralPart',
                 device_type: str = 'force-emitter',
                 **kwargs: 'Any') -> None:
        super().__init__(part, device_type=device_type)

    def act(self) -> None:

        structure = self.structural_part.structure

        if structure is None:
            return

        space = structure.space
        body = structure.body

        pos = self.structural_part.position
        segment_end = Vec2d(1000, 0)
        segment_end.angle = self.structural_part.angle

        collisions = space.segment_query(pos, pos + segment_end, 10,
                                         ShapeFilter())

        first_collision = next((col for col in collisions
                                if col.shape.body is not body), None)

        if first_collision is None:
            return

        force = Vec2d(-1000, 0)
        force.angle = self.structural_part.angle

        first_collision.shape.body.apply_force_at_world_point(
            force, first_collision.point)

        body.apply_force_at_world_point(force, pos)
