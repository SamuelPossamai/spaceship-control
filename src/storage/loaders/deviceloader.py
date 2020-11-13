
import functools
from typing import TYPE_CHECKING

from .customloader import CustomLoader
from .errorloader import loadError

from .. import configfilevariables

from ...utils.errorgenerator import ErrorGenerator

from ...devices.device import DeviceGroup
from ...devices.structure import StructuralPart
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

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    from typing import Sequence, Tuple, Any, MutableMapping, Iterable
    from PyQt5.QtWidgets import QWidget
    from ...devices.device import Device
    from ...devices.communicationdevices import CommunicationEngine
    # pylint: enable=ungrouped-imports


class DeviceLoader(CustomLoader):

    def __init__(self) -> None:
        super().__init__(self.__DEVICE_CREATE_FUNCTIONS, label='Device')

    def _getTypes(self, config: 'MutableMapping[str, Any]') -> 'Iterable[Any]': # pylint: disable=no-self-use

        function_type = config.get('function_type')
        type_ = config.get('type')
        models = config.get('model')

        if isinstance(models, list):
            types = []
            for model in models:
                types.append((function_type, type_, model))

            return types

        return ((function_type, type_, models), )

    def _addCustom(self, config: 'MutableMapping[str, Any]', model_type: 'Any',
                   model_info: 'MutableMapping[str, Any]') -> None:

        mode = config.get('mode')
        if mode == 'static':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomStaticDeviceFunction, model_info)
        elif mode is None or mode == 'dynamic':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicDeviceFunction, model_info)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    @staticmethod
    def __createCustomStaticDeviceFunction( # pylint: disable=no-self-use
            custom_device_info: 'MutableMapping[str, Any]',
            loader: 'DeviceLoader',
            info: 'MutableMapping[str, Any]', part: 'StructuralPart',
            **kwargs: 'Any') \
                -> 'Tuple[Device, Sequence[QWidget]]':

        return loader.load(custom_device_info.get('function_type'),
                           custom_device_info, part, **kwargs)

    @staticmethod
    def __createCustomDynamicDeviceFunction( # pylint: disable=no-self-use
            custom_device_info: 'MutableMapping[str, Any]',
            loader: 'DeviceLoader',
            info: 'MutableMapping[str, Any]', part: 'StructuralPart',
            **kwargs: 'Any') \
                -> 'Tuple[Device, Sequence[QWidget]]':

        variables = {variable['id']: variable['value'] for variable in
                     info.get('Variable', ())}

        configfilevariables.subVariables(custom_device_info,
                                         variables=variables,
                                         enabled=True)

        return loader.load(custom_device_info.get('function_type'),
                           custom_device_info, part, **kwargs)

    def load(self, device_type: str, info: 'MutableMapping[str, Any]',
             part: StructuralPart, device_group: 'DeviceGroup' = None,
             **kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        type_and_model = (device_type, info.get('type'), info.get('model'))
        create_func = self._load_functions.get(type_and_model)

        if create_func is None:
            type_and_model_str = f'{type_and_model[1]}/{type_and_model[2]}'
            raise ValueError((f'Invalid type/model for {device_type}'
                              f' \'{type_and_model_str}\'.'))

        device, widgets = create_func(self, info, part, **kwargs)

        if device_group is None:
            device_group = part

        device_group.addDevice(device, name=info.get('name'))

        return device, widgets

    def __loadErrorMutableMapping(
            self, errors: 'MutableMapping[str, MutableMapping[str, Any]]') \
                -> 'MutableMapping[str, ErrorGenerator]':

        return {name: loadError(info) for name, info in errors.items()
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

    def __sensorErrorKwargs(
            self, content: 'MutableMapping[str, MutableMapping[str, Any]]') \
                -> 'MutableMapping[str, ErrorGenerator]':

        return self.__getErrorKwargs(content, {
            'Read': 'read_error_gen'
        })

    def __createLinearEngine( # pylint: disable=no-self-use
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

    def __createForceEmitter( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        valid_keys = {'min_intensity', 'max_intensity', 'min_angle',
                      'max_angle'}

        fe_kwargs = {key: val for key, val in info.items() if key in valid_keys}

        return ForceEmitter(
            part,
            **fe_kwargs,
            **self.__engineErrorKwargs(info)), ()

    def __createPositionSensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return PositionSensor(part, info['reading_time'],
                              **self.__sensorErrorKwargs(info)), ()

    def __createAngleSensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return AngleSensor(part, info['reading_time'],
                           **self.__sensorErrorKwargs(info)), ()

    def __createSpeedSensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return SpeedSensor(part, info['reading_time'],
                           **self.__sensorErrorKwargs(info),
                           angle=info.get('angle', 0)), ()

    def __createVelocitySensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return VelocitySensor(part, info['reading_time'],
                              **self.__sensorErrorKwargs(info)), ()

    def __createAccelerationSensor(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                                   part: StructuralPart, **_kwargs: 'Any') \
            -> 'Tuple[Device, Sequence[QWidget]]':

        return AccelerationSensor(part, info['reading_time'],
                                  **self.__sensorErrorKwargs(info)), ()

    def __createAngularAccelerationSensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return (AngularAccelerationSensor(
            part, info['reading_time'], **self.__sensorErrorKwargs(info)), ())

    def __createAngularSpeedSensor(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                                   part: StructuralPart) \
                                       -> 'Tuple[Device, Sequence[QWidget]]':

        return AngularSpeedSensor(part, info['reading_time'],
                                  **self.__sensorErrorKwargs(info)), ()

    def __createObstacleDistanceSensor( # pylint: disable=no-self-use
            self, info: 'MutableMapping[str, Any]', part: StructuralPart,
            **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        return LineDetectSensor(part, info['reading_time'],
                                **self.__sensorErrorKwargs(info),
                                angle=info.get('angle'),
                                distance=info.get('distance')), ()

    def __createTextDisplay(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                            _part: StructuralPart,
                            **_kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        device = TextDisplayDevice()

        label = device.widget

        label.setGeometry(info.get('x', 0), info.get('y', 0),
                          info.get('width', 100), info.get('height', 30))

        return device, (label,)

    def __createConsole(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                        _part: StructuralPart,
                        **_kwargs: 'Any') -> 'Tuple[Device, Sequence[QWidget]]':

        device = ConsoleDevice(info.get('columns', 20), info.get('rows', 5))

        text = device.widget

        text.setGeometry(info.get('x', 0), info.get('y', 0),
                         info.get('width', 100), 0)

        return (device, (text,))

    def __createKeyboardReceiver(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                                 _part: StructuralPart,
                                 **_kwargs: 'Any') \
                                     -> 'Tuple[Device, Sequence[QWidget]]':

        device = KeyboardReceiverDevice()

        button = device.widget

        button.setGeometry(info.get('x', 0), info.get('y', 0), 20, 20)

        return device, (button,)

    def __createButton(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                       _part: StructuralPart,
                       **_kwargs: 'Any') \
                           -> 'Tuple[Device, Sequence[QWidget]]':

        device = ButtonDevice()

        button = device.widget

        button.setGeometry(info.get('x', 0), info.get('y', 0),
                           info.get('width', 20), info.get('height', 20))

        return device, (button,)

    def __createBasicReceiver(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
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

    def __createBasicSender(self, info: 'MutableMapping[str, Any]', # pylint: disable=no-self-use
                            part: StructuralPart,
                            engine: 'CommunicationEngine' = None,
                            **_kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        if engine is None:
            raise Exception('Communication module is present, but communication'
                            ' was not enabled')

        errors = self.__getErrorKwargs(info, {
            'Frequency': 'frequency_err_gen',
            'Intensity': 'intensity_err_gen'
        })

        return (BasicSender(part, engine, info['intensity'], info['frequency'],
                            **errors), ())

    def __createConfReceiver(self, info: 'MutableMapping[str, Any]',
                             part: StructuralPart,
                             engine: 'CommunicationEngine' = None,
                             **_kwargs: 'Any') \
                                 -> 'Tuple[Device, Sequence[QWidget]]':

        return ConfigurableReceiver(part, info.get('minimum_intensity', 0),
                                    info['frequency'],
                                    info.get('tolerance', 0.5),
                                    engine=engine), ()

    def __createConfSender(self, info: 'MutableMapping[str, Any]',
                           part: StructuralPart,
                           engine: 'CommunicationEngine' = None,
                           **_kwargs: 'Any') \
                               -> 'Tuple[Device, Sequence[QWidget]]':

        errors = self.__getErrorKwargs(info, {
            'Frequency': 'frequency_err_gen',
            'Intensity': 'intensity_err_gen'
        })

        return (ConfigurableSender(part, engine, info['intensity'],
                                   info['frequency'], **errors), ())

    def __createDeviceGroup(self, info: 'MutableMapping[str, Any]',
                            part: StructuralPart, **kwargs: 'Any') \
                                -> 'Tuple[Device, Sequence[QWidget]]':

        new_device = DeviceGroup()

        kwargs['device_group'] = new_device

        for device in info.get('Device', ()):
            self.load(device.get('kind', 'Sensor'), device, part, **kwargs)

        return new_device, ()

    __DEVICE_CREATE_FUNCTIONS: 'DeviceCreateFunctionsType' = {

        ('Actuator', 'engine', 'linear'): __createLinearEngine,
        ('Actuator', 'force-emitter', None): __createForceEmitter,
        ('Sensor', 'position', None): __createPositionSensor,
        ('Sensor', 'angle', None): __createAngleSensor,
        ('Sensor', 'speed', None): __createSpeedSensor,
        ('Sensor', 'angular-speed', None): __createAngularSpeedSensor,
        ('Sensor', 'velocity', None): __createVelocitySensor,
        ('Sensor', 'acceleration', None): __createAccelerationSensor,
        ('Sensor', 'angular-acceleration', None):
            __createAngularAccelerationSensor,
        ('Sensor', 'detect', 'linear-distance'): __createObstacleDistanceSensor,
        ('InterfaceDevice', 'text-display', None): __createTextDisplay,
        ('InterfaceDevice', 'text-display', 'line'): __createTextDisplay,
        ('InterfaceDevice', 'text-display', 'console'): __createConsole,
        ('InterfaceDevice', 'button', None): __createButton,
        ('InterfaceDevice', 'keyboard', None): __createKeyboardReceiver,
        ('Communication', 'receiver', None): __createBasicReceiver,
        ('Communication', 'sender', None): __createBasicSender,
        ('Communication', 'receiver', 'configurable'): __createConfReceiver,
        ('Communication', 'sender', 'configurable'): __createConfSender,
        ('DeviceGroup', None, None): __createDeviceGroup
    }
