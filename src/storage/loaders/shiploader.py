
from collections import namedtuple
from typing import TYPE_CHECKING, cast as typingcast

from pymunk import Body

from ...utils.errorgenerator import ErrorGenerator

from ...devices.structure import Structure, StructuralPart
from ...devices.sensors import (
    PositionSensor, AngleSensor, SpeedSensor, LineDetectSensor,
    AngularSpeedSensor, VelocitySensor, AccelerationSensor,
    AngularAccelerationSensor
)
from ...devices.engine import LinearEngine
from ...devices.forceemitter import ForceEmitter
from ...devices.interfacedevice import (
    TextDisplayDevice, ButtonDevice, KeyboardReceiverDevice, ConsoleDevice
)
from ...devices.communicationdevices import (
    BasicReceiver, BasicSender, ConfigurableReceiver, ConfigurableSender
)

from .shapeloader import loadShapes
from .imageloader import loadImages

if TYPE_CHECKING:
    from typing import (
        Tuple, Sequence, Any, MutableMapping, List, Callable, Optional
    )
    import pymunk
    from PyQt5.QtWidgets import QWidget
    from ...devices.device import Device
    from ...devices.communicationdevices import CommunicationEngine
    from ...devices.interfacedevice import InterfaceDevice

    CreateDeviceCallable = Callable[..., Tuple[Device, Sequence[QWidget]]]

    DeviceKindType = Tuple[Optional[str], Optional[str], Optional[str]]
    DeviceCreateFunctionsType = MutableMapping[DeviceKindType,
                                               CreateDeviceCallable]

ShipInfo = namedtuple('ShipInfo', ('device', 'images', 'widgets'))

def loadShip(ship_info: 'MutableMapping[str, Any]', name: str,
             space: 'pymunk.Space', prefixes: 'Sequence[str]' = (),
             communication_engine: 'Optional[CommunicationEngine]' = None) \
        -> 'ShipInfo':

    return ShipLoader().load(ship_info, name, space, prefixes=prefixes,
                             communication_engine=communication_engine)

class ShipLoader:

    def __init__(self) -> None:
        self.__create_functions = self.__DEVICE_CREATE_FUNCTIONS.copy()

    def clearCustomDeviceModels(self) -> None:
        self.__create_functions = self.__DEVICE_CREATE_FUNCTIONS.copy()

    def load(self, ship_info: 'MutableMapping[str, Any]', name: str,
             space: 'pymunk.Space', prefixes: 'Sequence[str]' = (),
             communication_engine: 'Optional[CommunicationEngine]' = None) \
        -> 'ShipInfo':

        shapes = loadShapes(ship_info['Shape'])

        mass = sum(shape.mass for shape in shapes)
        moment = sum(shape.moment for shape in shapes)

        if mass <= 0:
            raise Exception(f"Ship \'{name}\' has invalid mass")

        body = Body(mass, moment)

        for shape in shapes:
            shape.body = body

        space.add(body, shapes)

        ship, parts = self.__loadShipStructure(ship_info, name, space, body)

        for info in ship_info.get('Actuator', ()):
            self.__addDevice(info, parts, 'Actuator')

        for info in ship_info.get('Sensor', ()):
            self.__addDevice(info, parts, 'Sensor')

        for info in ship_info.get('Communication', ()):
            self.__addDevice(info, parts, 'Communication',
                             engine=communication_engine)

        widgets: 'List[QWidget]' = []
        for info in ship_info.get('InterfaceDevice', ()):
            widgets.extend(
                self.__addDevice(info, parts, 'InterfaceDevice'))

        return ShipInfo(device=ship, images=loadImages(
            ship_info.get('Image', ()), prefixes=prefixes), widgets=widgets)

    def __addDevice(
            self, info: 'MutableMapping[str, Any]',
            parts: 'MutableMapping[str, StructuralPart]',
            device_type: str, **kwargs: 'Any') -> 'Sequence[QWidget]':

        type_and_model = (device_type, info.get('type'), info.get('model'))
        create_func = self.__create_functions.get(type_and_model)

        part_name = typingcast(str, info.get('part'))
        part = parts.get(part_name)
        if part is None:
            raise Exception(f"{device_type} has invalid part \'{part_name}\'.")

        if create_func is None:
            type_and_model_str = f'{type_and_model[1]}/{type_and_model[2]}'
            raise ValueError(
                f'Invalid type/model for {device_type} \'{type_and_model_str}\'.')

        device, widgets = create_func(self, info, part, **kwargs)

        part.addDevice(device, name=info.get('name'))

        return widgets

    def __loadShipStructure(
            self, ship_info: 'MutableMapping[str, Any]', name: str,
            space: 'pymunk.Space', body: 'pymunk.Body') \
                -> 'Tuple[Structure, MutableMapping[str, StructuralPart]]':

        ship = Structure(name, space, body, device_type='ship')

        parts = {}
        for part_info in ship_info.get('Part', ()):
            part_name = str(part_info.get('name', 'unnamed'))
            part = StructuralPart(offset=(part_info['x'], part_info['y']))

            ship.addDevice(part, name=part_name)
            parts[part_name] = part

        return ship, parts

    def __loadError(self, info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        error_max = info.get('error_max', 0)

        if not isinstance(error_max, (int, float)):
            raise TypeError(
                f'error_max must be a number and not {type(error_max)}')

        offset_max = info.get('offset_max', 0)

        if not isinstance(offset_max, (int, float)):
            raise TypeError(
                f'offset_max must be a number and not {type(offset_max)}')

        error_max_minfac = info.get('error_max_minfac', 1)

        if not isinstance(error_max_minfac, (int, float)):
            raise TypeError('error_max_minfac must be a '
                            f'number and not {type(error_max_minfac)}')

        if error_max_minfac < 0 or error_max_minfac > 1:
            raise ValueError('error_max_minfac must be a value between 0 and 1'
                            f', {error_max_minfac} is not a valid value')

        return ErrorGenerator(error_max=error_max,
                            offset_max=offset_max,
                            error_max_minfac=error_max_minfac)

    def __loadErrorMutableMapping(
            self, errors: 'MutableMapping[str, MutableMapping[str, Any]]') \
                -> 'MutableMapping[str, ErrorGenerator]':

        return {name: self.__loadError(info) for name, info in errors.items()
                if not name.startswith('__')}

    def __getErrorKwargs(
        self, content: 'MutableMapping[str, MutableMapping[str, Any]]',
        errors: 'MutableMapping[str, str]') \
            -> 'MutableMapping[str, ErrorGenerator]':

        errors_content = content.get('Error')

        if errors_content is None:
            return {}

        errors_dict = self.__loadErrorMutableMapping(errors_content)

        return {key: value for key, value in
                ((error_keyword, errors_dict.get(error_tablename))
                for error_tablename, error_keyword in errors.items())
                if value is not None}

    def __engineErrorKwargs(
            self, content: 'MutableMapping[str, MutableMapping[str, Any]]') \
                -> 'MutableMapping[str, ErrorGenerator]':

        return self.__getErrorKwargs(content, {
            'Thrust': 'thrust_error_gen',
            'Angle': 'angle_error_gen',
            'Position': 'position_error_gen'
        })

    def __createLinearEngine(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return LinearEngine(
            part,
            info['min_intensity'],
            info['max_intensity'],
            info['min_angle'],
            info['max_angle'],
            intensity_multiplier=info.get('intensity_mult', 1),
            intensity_offset=info.get('intensity_offset', 0),
            **self.__engineErrorKwargs(info)), ()

    def __createForceEmitter(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        valid_keys = {'min_intensity', 'max_intensity', 'min_angle', 'max_angle'}

        fe_kwargs = {key: val for key, val in info.items() if key in valid_keys}

        return ForceEmitter(
            part,
            **fe_kwargs,
            **self.__engineErrorKwargs(info)), ()

    def __createPositionSensor(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return PositionSensor(part, info['reading_time'],
                            read_error_max=info.get('error_max', 0),
                            read_offset_max=info.get('offset_max', 0)), ()

    def __createAngleSensor(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return AngleSensor(part, info['reading_time'],
                        read_error_max=info.get('error_max', 0),
                        read_offset_max=info.get('offset_max', 0)), ()

    def __createSpeedSensor(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return SpeedSensor(part, info['reading_time'],
                        read_error_max=info.get('error_max', 0),
                        read_offset_max=info.get('offset_max', 0),
                        angle=info.get('angle', 0)), ()

    def __createVelocitySensor(
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return VelocitySensor(part, info['reading_time'],
                            read_error_max=info.get('error_max', 0),
                            read_offset_max=info.get('offset_max', 0)), ()

    def __createAccelerationSensor(self, info: 'MutableMapping[str, Any]',
                                part: StructuralPart,
                                **_kwargs: 'Any') \
            -> 'Tuple[Device, Sequence[QWidget]]':

        return AccelerationSensor(part, info['reading_time'],
                                read_error_max=info.get('error_max', 0),
                                read_offset_max=info.get('offset_max', 0)), ()

    def __createAngularAccelerationSensor(self, info: 'MutableMapping[str, Any]',
                                        part: StructuralPart,
                                        **_kwargs: 'Any') \
            -> 'Tuple[Device, Sequence[QWidget]]':

        return (AngularAccelerationSensor(
            part, info['reading_time'], read_error_max=info.get('error_max', 0),
            read_offset_max=info.get('offset_max', 0)), ())

    def __createAngularSpeedSensor(self, info: 'MutableMapping[str, Any]',
                                part: StructuralPart) \
                                    -> 'Tuple[Device, Sequence[QWidget]]':

        return AngularSpeedSensor(part, info['reading_time'],
                                read_error_max=info.get('error_max', 0),
                                read_offset_max=info.get('offset_max', 0)), ()

    def __createObstacleDistanceSensor(self, info: 'MutableMapping[str, Any]',
                                    part: StructuralPart,
                                    **_kwargs: 'Any') \
                                        -> 'Tuple[Device, Sequence[QWidget]]':

        return LineDetectSensor(part, info['reading_time'],
                                read_error_max=info.get('error_max', 0),
                                read_offset_max=info.get('offset_max', 0),
                                angle=info.get('angle'),
                                distance=info.get('distance')), ()

    def __createTextDisplay(self, info: 'MutableMapping[str, Any]',
                            _part: StructuralPart,
                            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        device = TextDisplayDevice()

        label = device.widget

        label.setGeometry(info.get('x', 0), info.get('y', 0),
                        info.get('width', 100), info.get('height', 30))

        return device, (label,)

    def __createConsole(self, info: 'MutableMapping[str, Any]', _part: StructuralPart,
                        **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        device = ConsoleDevice(info.get('columns', 20), info.get('rows', 5))

        text = device.widget

        text.setGeometry(info.get('x', 0), info.get('y', 0),
                        info.get('width', 100), 0)

        return (device, (text,))

    def __createKeyboardReceiver(self, info: 'MutableMapping[str, Any]',
                                _part: StructuralPart,
                                **_kwargs: 'Any') \
                                    -> 'Tuple[Device, Sequence[QWidget]]':

        device = KeyboardReceiverDevice()

        button = device.widget

        button.setGeometry(info.get('x', 0), info.get('y', 0), 20, 20)

        return device, (button,)

    def __createButton(self, info: 'MutableMapping[str, Any]', _part: StructuralPart,
                    **_kwargs: 'Any') \
                        -> 'Tuple[Device, Sequence[QWidget]]':

        device = ButtonDevice()

        button = device.widget

        button.setGeometry(info.get('x', 0), info.get('y', 0),
                        info.get('width', 20), info.get('height', 20))

        return device, (button,)

    def __createBasicReceiver(self, info: 'MutableMapping[str, Any]',
                            part: StructuralPart,
                            engine: 'CommunicationEngine' = None,
                            **_kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        if engine is None:
            raise Exception('Communication module is present, but communication'
                            ' was not enabled')

        return BasicReceiver(part, info.get('minimum_intensity', 0),
                            info['frequency'], info.get('tolerance', 0.5),
                            engine=engine), ()

    def __createBasicSender(self, info: 'MutableMapping[str, Any]', part: StructuralPart,
                            engine: 'CommunicationEngine' = None,
                            **_kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        if engine is None:
            raise Exception('Communication module is present, but communication'
                            ' was not enabled')

        errors = __getErrorKwargs(info, {
            'Frequency': 'frequency_err_gen',
            'Intensity': 'intensity_err_gen'
        })

        return (BasicSender(part, engine, info['intensity'], info['frequency'],
                            **errors), ())

    def __createConfReceiver(self, info: 'MutableMapping[str, Any]', part: StructuralPart,
                            engine: 'CommunicationEngine' = None,
                            **_kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        return ConfigurableReceiver(part, info.get('minimum_intensity', 0),
                                    info['frequency'], info.get('tolerance', 0.5),
                                    engine=engine), ()

    def __createConfSender(self, info: 'MutableMapping[str, Any]', part: StructuralPart,
                        engine: 'CommunicationEngine' = None,
                        **_kwargs: 'Any') \
                            -> 'Tuple[Device, Sequence[QWidget]]':

        errors = __getErrorKwargs(info, {
            'Frequency': 'frequency_err_gen',
            'Intensity': 'intensity_err_gen'
        })

        return (ConfigurableSender(part, engine, info['intensity'],
                                info['frequency'], **errors), ())

    __DEVICE_CREATE_FUNCTIONS: 'DeviceCreateFunctionsType' = {

        ('Actuator', 'engine', 'linear'): __createLinearEngine,
        ('Actuator', 'force-emitter', None): __createForceEmitter,
        ('Sensor', 'position', None): __createPositionSensor,
        ('Sensor', 'angle', None): __createAngleSensor,
        ('Sensor', 'speed', None): __createSpeedSensor,
        ('Sensor', 'angular-speed', None): __createAngularSpeedSensor,
        ('Sensor', 'velocity', None): __createVelocitySensor,
        ('Sensor', 'acceleration', None): __createAccelerationSensor,
        ('Sensor', 'angular-acceleration', None): __createAngularAccelerationSensor,
        ('Sensor', 'detect', 'linear-distance'): __createObstacleDistanceSensor,
        ('InterfaceDevice', 'text-display', None): __createTextDisplay,
        ('InterfaceDevice', 'text-display', 'line'): __createTextDisplay,
        ('InterfaceDevice', 'text-display', 'console'): __createConsole,
        ('InterfaceDevice', 'button', None): __createButton,
        ('InterfaceDevice', 'keyboard', None): __createKeyboardReceiver,
        ('Communication', 'receiver', None): __createBasicReceiver,
        ('Communication', 'sender', None): __createBasicSender,
        ('Communication', 'receiver', 'configurable'): __createConfReceiver,
        ('Communication', 'sender', 'configurable'): __createConfSender
    }
