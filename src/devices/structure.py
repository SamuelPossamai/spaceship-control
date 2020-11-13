
from abc import abstractmethod
import time
import math
from typing import TYPE_CHECKING, cast as typingcast

from .device import DeviceGroup, DefaultDevice

from ..utils.errorgenerator import NormalDistributionErrorGenerator

if TYPE_CHECKING:
    from typing import Any, Dict, Type, List, Tuple, Callable, Optional
    import pymunk
    from .device import Device

class Structure(DeviceGroup):
    """Class that represents a ship

    A Structure object is used to represent the ship's devices and control
    interface, this class is used so the controller can give commands for
    the actuators and sensors. An object of this class is connected to the
    physical engine so the sensors and actuators connected to it can perform
    their functions.

    Args:
        name: Name used to identify the ship.
        space: Representation of the space in the physical engine.
        body: Representation of the ship static and dynamic physical properties.
    """

    def __init__(self, name: str, space: 'pymunk.Space', body: 'pymunk.Body',
                 **kwargs: 'Any') -> None:

        if 'device_type' not in kwargs:
            kwargs['device_type'] = 'structure'

        super().__init__(**kwargs)

        self.__body = body
        self.__space = space
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    def addDevice(self, device: 'Device', name: str = None) -> None:
        super().addDevice(device, name)

        if isinstance(device, StructuralPart):
            device.structure = self

    def isDestroyed(self) -> bool:
        return self.__body.space is None

    @property
    def body(self) -> 'pymunk.Body':
        return self.__body

    @property
    def space(self) -> 'pymunk.Space':
        return self.__space

class StructuralPart(DeviceGroup):

    def __init__(self,
                 structure: Structure = None,
                 offset: 'Tuple[float, float]' = (0, 0),
                 **kwargs: 'Any') -> None:

        if 'device_type' not in kwargs:
            kwargs['device_type'] = 'structural-part'

        super().__init__(**kwargs)

        self.__offset = offset
        self.__structure = structure

    def applyForce(self, val, x_pos, y_pos, angle) -> None:

        if self.__structure is None:
            return

        body = self.__structure.body

        offset = (x_pos + self.__offset[0], y_pos + self.__offset[1])

        body.apply_impulse_at_local_point((math.cos(angle)*val,
                                           math.sin(angle)*val), offset)

    @property
    def position(self) -> 'Tuple[float, float]':
        if self.__structure is None:
            return self.__offset
        pos = self.__structure.body.position
        return pos.x + self.__offset[0], pos.y + self.__offset[1]

    @property
    def angle(self) -> float:
        if self.__structure is None:
            return 0
        return typingcast(float, self.__structure.body.angle)

    @property
    def velocity(self) -> 'Tuple[float, float]':
        if self.__structure is None:
            return 0

        velocity = self.__structure.body.velocity
        return velocity.x, velocity.y

    @property
    def angular_velocity(self) -> float:
        if self.__structure is None:
            return 0

        return self.__structure.body.angular_velocity

    @property
    def structure(self) -> 'Optional[Structure]':
        return self.__structure

    @structure.setter
    def structure(self, structure: Structure) -> None:
        self.__structure = structure

    @property
    def offset(self) -> 'Tuple[float, float]':
        return self.__offset

class Sensor(DefaultDevice):

    def __init__(self, st_part: StructuralPart,
                 read_time: float,
                 read_error_gen: 'ErrorGenerator' = None,
                 **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__st_part = st_part
        self.__last_read_time: float = 0
        self.__last_value: float = 0
        self.__read_time = read_time
        self.__error_gen = read_error_gen

    @property
    def structural_part(self) -> StructuralPart:
        return self.__st_part

    @property
    def reading_time(self) -> float:
        return self.__read_time

    @property
    def max_read_error(self) -> float: # TODO: replace this using getDict method
        return self.__error_gen.max_error + self.__error_gen.max_offset

    @property
    def max_read_offset(self) -> float:
        return self.__error_gen.max_offset

    def act(self) -> None:
        pass

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, Sensor.__COMMANDS, *args)

    def __read(self) -> float:
        now = time.time()

        if now - self.__last_read_time > self.__read_time:

            read_val = self.read()
            if self.__error_gen:
                self.__last_value = self.__error_gen(read_val)
            else:
                self.__last_value = read_val
            self.__last_read_time = now

        return self.__last_value

    @abstractmethod
    def read(self) -> float:
        pass

    __COMMANDS = {

        'read': __read,
        'reading-time': reading_time.fget,
        'max-error': max_read_error.fget,
        'max-offset': max_read_offset.fget
    }

class MultiSensor(DeviceGroup):

    def __init__(self, sensors: 'Dict[str, Type[Sensor]]',
                 st_part: 'StructuralPart',
                 read_time: float,
                 read_error_gen: 'ErrorGenerator' = None,
                 **kwargs: 'Any'):
        super().__init__(**kwargs)

        self.__sensors = []
        for sensor_name, sensor_type in sensors.items():
            self.__sensors.append(sensor_type(st_part, read_time,
                                              read_error_gen=read_error_gen))
            self.addDevice(self.__sensors[-1], name=sensor_name)

    def command(self, command: 'List[str]', *args) -> 'Any':
        if self.__sensors and command and \
            command[0] in MultiSensor.__REDIRECT_COMMANDS:

            return self.__sensors[0].command(command)

        return super().command(command, *args)

    __REDIRECT_COMMANDS = {'reading-time', 'max-error', 'max-offset'}

class Actuator(DefaultDevice):

    def __init__(self, part: StructuralPart, **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__part = part

    def applyForce(self, val, x_pos, y_pos, angle) -> None:
        self.__part.applyForce(val, x_pos, y_pos, angle)

    @property
    def structural_part(self) -> StructuralPart:
        return self.__part

    def act(self) -> None:
        self.actuate()

    @abstractmethod
    def actuate(self) -> None:
        pass
