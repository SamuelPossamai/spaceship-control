
from typing import TYPE_CHECKING, cast as typingcast

from pymunk import Vec2d, ShapeFilter

from math import pi, cos, sin

from .structure import Sensor, MultiSensor

if TYPE_CHECKING:
    from typing import Any, Union

class XPositionSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='x-position-sensor', **kwargs)

    def read(self) -> float:
        x, _ = self.structural_part.position
        return x

class YPositionSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='y-position-sensor', **kwargs)

    def read(self) -> float:
        _, y = self.structural_part.position
        return y

class PositionSensor(MultiSensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__({'x': XPositionSensor, 'y': YPositionSensor},
                         *args, device_type='position-sensor', **kwargs)

class AngleSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='angle-sensor', **kwargs)

    def read(self) -> float:
        return 180*self.structural_part.angle/pi

class SpeedSensor(Sensor):

    def __init__(self, *args: 'Any', angle: 'Union[float, int]' = 0,
                 **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='speed-sensor', **kwargs)

        self.__off_angle = angle

    def read(self) -> float:
        vel = self.structural_part.velocity
        angle = self.__off_angle + self.structural_part.angle
        return vel[0]*cos(angle) + vel[1]*sin(angle)

class AngularSpeedSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='ang-speed-sensor', **kwargs)

    def read(self) -> float:
        return 180*self.structural_part.angular_velocity/pi

class XAccelerationSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='x-acceleration-sensor', **kwargs)
        self.__last_x_speed = 0
        self.__last_acc_val = 0

    def act(self):
        current_speed = self.structural_part.velocity.x
        self.__last_acc_val = current_speed - self.__current_x_speed
        self.__last_x_speed = current_speed

    def read(self) -> float:
        return self.__last_acc_val

class YAccelerationSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='y-acceleration-sensor', **kwargs)
        self.__last_y_speed = 0

    def act(self):
        current_speed = self.structural_part.velocity.y
        self.__last_acc_val = current_speed - self.__current_y_speed
        self.__last_y_speed = current_speed

    def read(self) -> float:
        return self.__last_acc_val

class AccelerationSensor(MultiSensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__({'x': XAccelerationSensor, 'y': YAccelerationSensor},
                         *args, device_type='acceleration-sensor', **kwargs)

class AngularAccelerationSensor(Sensor):

    def __init__(self, *args: 'Any', **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='ang-acceleration-sensor', **kwargs)
        self.__last_ang_speed = 0

    def act(self):
        current_speed = 180*self.structural_part.angular_velocity/pi
        self.__last_acc_val = current_speed - self.__last_ang_speed
        self.__last_ang_speed = current_speed

    def read(self) -> float:
        return self.__last_acc_val

class LineDetectSensor(Sensor):

    def __init__(self, *args: 'Any', distance: float = None,
                 angle: float = None, **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='line-dist-sensor', **kwargs)

        self.__max_dist = 1000 if distance is None else distance
        self.__angle = 0 if angle is None else pi*angle/180

    def read(self) -> float:

        structure = self.structural_part.structure

        if structure is None:
            return self.__max_dist

        space = structure.space
        body = structure.body

        pos = self.structural_part.position
        segment_end = Vec2d(self.__max_dist, 0)
        segment_end.angle = self.structural_part.angle + self.__angle

        collisions = space.segment_query(pos, pos + segment_end, 10,
                                         ShapeFilter())

        first_collision = next((col for col in collisions
                                if col.shape.body is not body), None)

        if first_collision is None:
            return self.__max_dist

        return typingcast(float, first_collision.point.get_distance(pos))

class DetectCloserSensor(Sensor):

    def __init__(self, *args: 'Any', distance: float = None,
                 **kwargs: 'Any') -> None:
        super().__init__(*args, device_type='dist-sensor', **kwargs)

        self.__max_dist = 1000 if distance is None else distance

    def read(self) -> float:

        structure = self.structural_part.structure

        if structure is None:
            return self.__max_dist

        space = structure.space
        body = structure.body

        pos = self.structural_part.position

        collisions = space.point_query(pos, self.__max_dist, ShapeFilter())

        first_collision = next((col for col in collisions
                                if col.shape.body is not body), None)

        if first_collision is None:
            return self.__max_dist

        return typingcast(float, first_collision.distance)
