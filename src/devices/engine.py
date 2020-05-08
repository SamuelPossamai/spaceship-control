
from abc import abstractmethod

from .structure import Actuator
from ..utils.interval import Interval, IntervalSet

class Engine(Actuator):

    class Mirror(Actuator.Mirror):

        def __init__(self, device: 'Device', *args: str) -> None:
            super().__init__(device, 'intensity', 'angle', *args)

    def __init__(self, part: 'StructuralPart', **kwargs):
        super().__init__(part, properties={'intensity': Engine.intensity,
                                           'angle': Engine.angle})

        self.__intensity = kwargs.get('start_intensity', 0)
        self.__thrust = self.mapIntensityToThrust(self.__intensity)
        self.__angle = kwargs.get('start_angle', 0)
        self.__thrust_error = kwargs.get('thrust_error_gen')
        self.__angle_error = kwargs.get('angle_error_gen')
        self.__pos_error = kwargs.get('position_error_gen')
        self.__valid_intensities = kwargs.get('valid_intensities')
        self.__valid_angles = kwargs.get('valid_angles')

    @property
    def intensity(self):
        return self.__intensity

    @intensity.setter
    def intensity(self, val):

        if isinstance(val, str):
            val = float(val)

        if self.__valid_intensities is None or \
            self.__valid_intensities.isInside(val):

            self.__intensity = val
            self.__thrust = self.mapIntensityToThrust(self.__intensity)

    @property
    def angle(self):
        return self.__angle

    @angle.setter
    def angle(self, val):

        if isinstance(val, str):
            val = float(val)

        if self.__valid_angles is None or \
            self.__valid_angles.isInside(val):

            self.__angle = val

    @abstractmethod
    def mapIntensityToThrust(self, intensity) -> 'Union[float, int]':
        pass

    def actuate(self) -> None:

        if self.__thrust_error is None:
            thrust = self.__thrust
        else:
            thrust = self.__thrust_error(self.__thrust)

        if self.__angle_error is None:
            angle = self.__angle
        else:
            angle = self.__angle_error(self.__angle_error)

        if self.__pos_error is None:
            x_pos = y_pos = 0
        else:
            x_pos = self.__pos_error(0)
            y_pos = self.__pos_error(0)

        self.applyForce(thrust, x_pos, y_pos, angle)

    @property
    def mirror(self) -> 'Engine.Mirror':
        return Engine.Mirror(self)

class LinearEngine(Engine):

    def __init__(self, part: 'StructuralPart',
                 intensity_multiplier: 'Union[float, int]' = 1,
                 intensity_offset: 'Union[float, int]' = 0,
                 **kwargs: 'Any') -> None:

        self.__int_mult = intensity_multiplier
        self.__int_off = intensity_offset

        super().__init__(part, **kwargs)

    def mapIntensityToThrust(self, intensity) -> 'Union[float, int]':
        return self.__int_off + intensity*self.__int_mult

class LimitedLinearEngine(LinearEngine):

    def __init__(self, part: 'StructuralPart',
                 min_intensity: 'Union[float, int]',
                 max_intensity: 'Union[float, int]',
                 min_angle: 'Union[float, int]',
                 max_angle: 'Union[float, int]',
                 **kwargs: 'Any') -> None:

        valid_intensities = IntervalSet((Interval(min_intensity,
                                                  max_intensity),))
        valid_angles = IntervalSet((Interval(min_angle,
                                             max_angle),))

        super().__init__(part, valid_intensities=valid_intensities,
                         valid_angles=valid_angles, **kwargs)
