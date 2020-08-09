
from collections import namedtuple
from typing import TYPE_CHECKING, cast as typingcast

from pymunk import Body

from ...utils.errorgenerator import ErrorGenerator

from ...devices.structure import Structure, StructuralPart
from ...devices.sensors import (
    PositionSensor, AngleSensor, SpeedSensor, LineDetectSensor,
    AngularSpeedSensor
)
from ...devices.engine import LinearEngine
from ...devices.interfacedevice import (
    TextDisplayDevice, ButtonDevice, KeyboardReceiverDevice, ConsoleDevice
)
from ...devices.communicationdevices import (
    BasicReceiver, BasicSender, ConfigurableReceiver, ConfigurableSender
)

from .shapeloader import loadShapes
from .imageloader import loadImages

if TYPE_CHECKING:
    from typing import Tuple, Sequence, Any, Dict, List, Callable, Optional
    import pymunk
    from PyQt5.QtWidgets import QWidget
    from ...devices.device import Device
    from ...devices.communicationdevices import CommunicationEngine
    from ...devices.interfacedevice import InterfaceDevice

    CreateDeviceCallable = Callable[..., Tuple[Device, Sequence[QWidget]]]

    DeviceKindType = Tuple[Optional[str], Optional[str], Optional[str]]
    DeviceCreateFunctionsType = Dict[DeviceKindType, CreateDeviceCallable]

ShipInfo = namedtuple('ShipInfo', ('device', 'images', 'widgets'))

def __loadError(info: 'Dict[str, Any]') -> ErrorGenerator:

    return ErrorGenerator(error_max=info.get('error_max'),
                          offset_max=info.get('offset_max'),
                          error_max_minfac=info.get('error_max_minfac', 1))

def __loadErrorDict(
        errors: 'Dict[str, Dict[str, Any]]') -> 'Dict[str, ErrorGenerator]':

    return {name: __loadError(info) for name, info in errors.items()
            if not name.startswith('__')}

def __getErrorKwargs(content: 'Dict[str, Dict[str, Any]]',
                     errors: 'Dict[str, str]') -> 'Dict[str, ErrorGenerator]':

    errors_content = content.get('Error')

    if errors_content is None:
        return {}

    errors_dict = __loadErrorDict(errors_content)

    return {key: value for key, value in
            ((error_keyword, errors_dict.get(error_tablename))
             for error_tablename, error_keyword in errors.items())
            if value is not None}

def __engineErrorKwargs(
        content: 'Dict[str, Dict[str, Any]]') -> 'Dict[str, ErrorGenerator]':

    return __getErrorKwargs(content, {
        'Thrust': 'thrust_error_gen',
        'Angle': 'angle_error_gen',
        'Position': 'position_error_gen'
    })

def __createLinearEngine(info: 'Dict[str, Any]', part: StructuralPart,
                         **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return LinearEngine(
        part,
        info['min_intensity'],
        info['max_intensity'],
        info['min_angle'],
        info['max_angle'],
        intensity_multiplier=info.get('intensity_mult', 1),
        intensity_offset=info.get('intensity_offset', 0),
        **__engineErrorKwargs(info)), ()

def __createPositionSensor(info: 'Dict[str, Any]', part: StructuralPart,
                           **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return PositionSensor(part, info['reading_time'],
                          read_error_max=info.get('error_max', 0),
                          read_offset_max=info.get('offset_max', 0)), ()

def __createAngleSensor(info: 'Dict[str, Any]', part: StructuralPart,
                        **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return AngleSensor(part, info['reading_time'],
                       read_error_max=info.get('error_max', 0),
                       read_offset_max=info.get('offset_max', 0)), ()

def __createSpeedSensor(info: 'Dict[str, Any]', part: StructuralPart,
                        **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return SpeedSensor(part, info['reading_time'],
                       read_error_max=info.get('error_max', 0),
                       read_offset_max=info.get('offset_max', 0),
                       angle=info.get('angle', 0)), ()

def __createAngularSpeedSensor(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return AngularSpeedSensor(part, info['reading_time'],
                              read_error_max=info.get('error_max', 0),
                              read_offset_max=info.get('offset_max', 0)), ()

def __createObstacleDistanceSensor(info: 'Dict[str, Any]', part: StructuralPart,
                                   **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return LineDetectSensor(part, info['reading_time'],
                            read_error_max=info.get('error_max', 0),
                            read_offset_max=info.get('offset_max', 0),
                            angle=info.get('angle'),
                            distance=info.get('distance')), ()

def __createTextDisplay(info: 'Dict[str, Any]', _part: StructuralPart,
                        **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    device = TextDisplayDevice()

    label = device.widget

    label.setGeometry(info.get('x', 0), info.get('y', 0),
                      info.get('width', 100), info.get('height', 30))

    return device, (label,)

def __createConsole(info: 'Dict[str, Any]', _part: StructuralPart,
                    **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    device = ConsoleDevice(info.get('columns', 20), info.get('rows', 5))

    text = device.widget

    text.setGeometry(info.get('x', 0), info.get('y', 0),
                     info.get('width', 100), 0)

    return (device, (text,))

def __createKeyboardReceiver(info: 'Dict[str, Any]', _part: StructuralPart,
                             **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    device = KeyboardReceiverDevice()

    button = device.widget

    button.setGeometry(info.get('x', 0), info.get('y', 0), 20, 20)

    return device, (button,)

def __createButton(info: 'Dict[str, Any]', _part: StructuralPart, **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    device = ButtonDevice()

    button = device.widget

    button.setGeometry(info.get('x', 0), info.get('y', 0),
                       info.get('width', 20), info.get('height', 20))

    return device, (button,)

def __createBasicReceiver(info: 'Dict[str, Any]', part: StructuralPart,
                          engine: 'CommunicationEngine' = None, **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return BasicReceiver(part, info.get('minimum_intensity', 0),
                         info['frequency'], info.get('tolerance', 0.5),
                         engine=engine), ()

def __createBasicSender(info: 'Dict[str, Any]', part: StructuralPart,
                        engine: 'CommunicationEngine' = None, **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    errors = __getErrorKwargs(info, {
        'Frequency': 'frequency_err_gen',
        'Intensity': 'intensity_err_gen'
    })

    return (BasicSender(part, engine, info['intensity'], info['frequency'],
                        **errors), ())

def __createConfReceiver(info: 'Dict[str, Any]', part: StructuralPart,
                         engine: 'CommunicationEngine' = None, **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    return ConfigurableReceiver(part, info.get('minimum_intensity', 0),
                                info['frequency'], info.get('tolerance', 0.5),
                                engine=engine), ()

def __createConfSender(info: 'Dict[str, Any]', part: StructuralPart,
                       engine: 'CommunicationEngine' = None, **_kwargs) \
    -> 'Tuple[Device, Sequence[QWidget]]':

    errors = __getErrorKwargs(info, {
        'Frequency': 'frequency_err_gen',
        'Intensity': 'intensity_err_gen'
    })

    return (ConfigurableSender(part, engine, info['intensity'],
                               info['frequency'], **errors), ())

__DEVICE_CREATE_FUNCTIONS: 'DeviceCreateFunctionsType' = {

    ('Actuator', 'engine', 'linear'): __createLinearEngine,
    ('Sensor', 'position', None): __createPositionSensor,
    ('Sensor', 'angle', None): __createAngleSensor,
    ('Sensor', 'speed', None): __createSpeedSensor,
    ('Sensor', 'angular-speed', None): __createAngularSpeedSensor,
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

def __addDevice(
        info: 'Dict[str, Any]', parts: 'Dict[str, StructuralPart]',
        device_type: str, **kwargs) -> 'Sequence[QWidget]':

    type_and_model = (device_type, info.get('type'), info.get('model'))
    create_func = __DEVICE_CREATE_FUNCTIONS.get(type_and_model)

    part_name = typingcast(str, info.get('part'))
    part = parts.get(part_name)
    if part is None:
        raise Exception(f"{device_type} has invalid part \'{part_name}\'.")

    if create_func is None:
        type_and_model_str = f'{type_and_model[1]}/{type_and_model[2]}'
        raise ValueError(
            f'Invalid type/model for {device_type} \'{type_and_model_str}\'.')

    device, widgets = create_func(info, part, **kwargs)

    part.addDevice(device, name=info.get('name'))

    return widgets

def __loadShipStructure(ship_info, name, space, body):

    ship = Structure(name, space, body, device_type='ship')

    parts = {}
    for part_info in ship_info.get('Part', ()):
        part_name = part_info['name']
        part = StructuralPart(offset=(part_info['x'], part_info['y']))

        ship.addDevice(part, name=part_name)
        parts[part_name] = part

    return ship, parts

def loadShip(ship_info: 'Dict[str, Any]', name: str, space: 'pymunk.Space',
             prefixes: 'Sequence[str]' = (), communication_engine=None) \
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

    ship, parts = __loadShipStructure(ship_info, name, space, body)

    for info in ship_info.get('Actuator', ()):
        __addDevice(info, parts, 'Actuator')

    for info in ship_info.get('Sensor', ()):
        __addDevice(info, parts, 'Sensor')

    for info in ship_info.get('Communication', ()):
        __addDevice(info, parts, 'Communication', engine=communication_engine)

    widgets: 'List[QWidget]' = []
    for info in ship_info.get('InterfaceDevice', ()):
        widgets.extend(
            __addDevice(info, parts, 'InterfaceDevice'))

    return ShipInfo(device=ship, images=loadImages(
        ship_info.get('Image', ()), prefixes=prefixes), widgets=widgets)
