
from pymunk import Vec2d, ShapeFilter

from math import pi, cos, sin

from .structure import Sensor, MultiSensor

class XPositionSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='x-position-sensor', **kwargs)

    def read(self):
        x, _ = self.structural_part.position
        return x

class YPositionSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='y-position-sensor', **kwargs)

    def read(self):
        _, y = self.structural_part.position
        return y

class PositionSensor(MultiSensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__({'x': XPositionSensor, 'y': YPositionSensor},
                         *args, device_type='position-sensor', **kwargs)

class AngleSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='angle-sensor', **kwargs)

    def read(self):
        return 180*self.structural_part.angle/pi

class SpeedSensor(Sensor):

    def __init__(self, *args: 'Any', angle: 'Union[float, int]' = 0,
                 **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='speed-sensor', **kwargs)

        self.__off_angle = angle

    def read(self):
        vel = self.structural_part.velocity
        angle = self.__off_angle + self.structural_part.angle
        return vel[0]*cos(angle) + vel[1]*sin(angle)

class LineDetectSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='line-dist-sensor', **kwargs)

    def read(self):
        structure = self.structural_part.structure
        space = structure.space

        dist_max = 1000

        pos = self.structural_part.position
        segment_end = Vec2d(dist_max, 0)
        segment_end.angle = self.structural_part.angle

        result = space.segment_query_first(pos, pos + segment_end, 1,
                                           ShapeFilter())

        if result.shape is None:
            return dist_max

        return result.point.get_distance(pos)
