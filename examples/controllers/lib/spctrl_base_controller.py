#!/usr/bin/env python3

import sys
import time

import collections

from abc import ABC, abstractmethod

from PyQt5.QtCore import Qt

__device_comm_write = sys.__stdout__
__device_comm_read = sys.__stdin__

class Device(ABC):

    _DEVICE_TYPE_MAP = {}

    def __init__(self, device_path='', parent=None):

        if isinstance(device_path, Device):
            parent = device_path.parent
            device_path = device_path.device_path

        self.__device_path = device_path
        self.__parent = parent

        if self.sendMessage('get-info is-device-group') == 'yes':

            children_count = int(self.sendMessage('device-count'))

            if device_path == '':
                dev_path_prefix = ':'
            else:
                dev_path_prefix = device_path

            children = []
            for i in range(children_count):
                child_type = self.sendMessage(f'{i}: device-type')
                child_class = self._DEVICE_TYPE_MAP.get(child_type, Device)
                children.append(child_class(
                    device_path=f'{device_path}{i}:', parent=self))

            self.__children = tuple(children)
        else:
            self.__children = None

        self.__device_type = self.sendMessage('device-type')
        self.__device_desc = self.sendMessage('device-desc')
        self.__device_name = self.sendMessage(
            'get-info device-name-in-group')
        if self.__device_name == '<<null>>':
            self.__device_name = self.__device_type

    @property
    def device_path(self):
        return self.__device_path

    @property
    def parent(self):
        return self.__parent

    @property
    def children(self):
        return self.__children

    @property
    def type_(self):
        return self.__device_type

    @property
    def name(self):
        return self.__device_name

    @property
    def description(self):
        return self.__device_desc

    def __get_repr(self, depth=0):

        spaces = '  '*depth
        prefix = spaces + self.__device_name

        if self.__children is None:
            return prefix

        children_repr = (child.__get_repr(depth+1) for child in self.__children)
        return prefix + ': {\n' + ',\n'.join(children_repr) + f'\n{spaces}}}'

    def __repr__(self):
        return self.__get_repr()

    def sendMessage(self, message):
        return send(self.__device_path + message)

class Engine(Device):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__intensity = None

    @property
    def intensity(self):
        if self.__intensity is None:
            self.__intensity = self.sendMessage('get-property intensity')

        return self.__intensity

    @intensity.setter
    def intensity(self, value):
        self.__intensity = None
        self.sendMessage(f'set-property intensity {value}')

Device._DEVICE_TYPE_MAP['engine'] = Engine
Device._DEVICE_TYPE_MAP['linear-engine'] = Engine

class Sensor(Device):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.__reading_time = float(self.sendMessage('reading-time'))
            self.__max_offset = float(self.sendMessage('max-offset'))
            self.__max_error = float(
                self.sendMessage('max-error')) - self.__max_offset
        except ValueError:
            self.__reading_time = self.__max_offset = self.__max_error = None

    @property
    def reading_time(self):
        return self.__reading_time

    @property
    def max_error(self):
        return self.__max_error

    @property
    def max_offset(self):
        return self.__max_offset

    def read(self, subdevice=None):
        if subdevice is None:
            msg = 'read'
        else:
            msg = f'{subdevice}:read'

        try:
            return float(self.sendMessage(msg))
        except ValueError:
            return float('NaN')

Device._DEVICE_TYPE_MAP['position-sensor'] = Sensor
Device._DEVICE_TYPE_MAP['angle-sensor'] = Sensor
Device._DEVICE_TYPE_MAP['speed-sensor'] = Sensor
Device._DEVICE_TYPE_MAP['ang-speed-sensor'] = Sensor
Device._DEVICE_TYPE_MAP['line-dist-sensor'] = Sensor

SensorInfo = collections.namedtuple('SensorInfo', (
    'reading_time', 'max_error', 'max_offset', 'estimated_offset'))

class TextInputDevice(Device):

    @abstractmethod
    def read(self, size=-1):
        pass

    @abstractmethod
    def readline(self):
        pass

    def flush(self):
        pass

class SimpleKeyboardInputDevice(TextInputDevice):

    def __init__(self, device_path='', parent=None):
        super().__init__(device_path=device_path, parent=parent)

        self.__buffer = None

    def read(self, size=-1):

        if self.__buffer is None:
            self.__buffer = self.__read()
        elif size < 0 or len(self.__buffer) < size:
            self.__buffer += self.__read()

        if size < 0 or len(self.__buffer) < size:
            read_content = self.__buffer
            self.__buffer = None
            return read_content

        read_content = self.__buffer[:size]
        self.__buffer = self.__buffer[size:]

        return read_content

    def readline(self):
        return self.read()

    def flush(self):
        pass

    def _returnToBuffer(self, text):
        if self.__buffer is None:
            self.__buffer = text
        else:
            self.__buffer = text + self.__buffer

    def __read(self):
        return self.sendMessage('get')

Device._DEVICE_TYPE_MAP['keyboard'] = SimpleKeyboardInputDevice

class TranslatedKeyboardInputDevice(SimpleKeyboardInputDevice):

    Key = collections.namedtuple('Key', (
        'char', 'code', 'modifiers', 'shift', 'control'))

    def read(self, size=-1, end_at=None):
        content = super().read(size)
        key_list = []

        for i in range(0, len(content) - 9, 10):

            key_content = int(content[i: i+10], 16)

            key_modifiers = key_content >> 8
            key_code = key_content & 0xffffffff

            shift_up = key_modifiers & Qt.ShiftModifier

            key_char = None
            if key_code >= Qt.Key_Space and key_code <= Qt.Key_AsciiTilde:
                ascii_code = key_code
                if not shift_up:
                    if key_code >= Qt.Key_A and key_code <= Qt.Key_Z:
                        ascii_code = key_code + ord('a') - ord('A')
                key_char = chr(ascii_code)

            elif key_code == Qt.Key_Return:
                key_char = '\n'

            key_list.append(self.Key(
                char=key_char,
                code=key_code,
                modifiers=key_modifiers,
                shift=shift_up,
                control=key_modifiers & Qt.ControlModifier
            ))

            if end_at is not None:
                if key_char == end_at or key_code == end_at:
                    self._returnToBuffer(content[i+10:])
                    return key_list

        return key_list

    def readline(self):
        return self.read(end_at='\n')

class TextOutputDevice(Device):

    @abstractmethod
    def write(self, text):
        pass

    def flush(self):
        pass

_SimpleConsoleOutputDevice_WriteMode = collections.namedtuple(
    'WriteMode', ('Normal', 'Push', 'Static'))

class SimpleConsoleOutputDevice(TextOutputDevice):

    WriteMode = _SimpleConsoleOutputDevice_WriteMode

    def __init__(self, device_path='', parent=None):
        super().__init__(device_path=device_path, parent=parent)

        self.__message_buffer = ''
        self.__current_message_mode = \
            SimpleConsoleOutputDevice.WriteMode.Normal;

    def write(self, text, mode=_SimpleConsoleOutputDevice_WriteMode.Normal):

        if mode is not self.__current_message_mode:
            if not self.__message_buffer:
                self.flush()
            self.__current_message_mode = mode

        self.__message_buffer += text

    def flush(self):

        if not self.__message_buffer:
            return

        self.__message_buffer = \
            self.__message_buffer.replace('\\', '\\\\').replace('"', '\\"')

        messages = iter(self.__message_buffer.split('\n'))

        self.__printMsg(next(messages))
        for message in messages:
            self.sendMessage('LF')
            if message:
                self.__printMsg(message)

        self.sendMessage('update')
        self.__message_buffer = ''

    def clear(self):
        self.sendMessage('clear')
        self.sendMessage('set-cursor-pos 0 0')
        self.__message_buffer = ''

    def __printMsg(self, text):

        if self.__current_message_mode is \
                SimpleConsoleOutputDevice.WriteMode.Normal:
            cmd = 'write'
        elif self.__current_message_mode is \
                SimpleConsoleOutputDevice.WriteMode.Static:
            cmd = 'static-write'
        elif self.__current_message_mode is \
                SimpleConsoleOutputDevice.WriteMode.Push:
            cmd = 'push-write'
        else:
            cmd = 'write'

        self.sendMessage(f'{cmd} "{text}"')

Device._DEVICE_TYPE_MAP['console-text-display'] = SimpleConsoleOutputDevice

class Ship:

    class ConsolePrinter:

        def __init__(self, ship):
            self.__ship = ship

        def write(self, text):
            self.__ship.writeConsole(text)

        def flush(self):
            pass

    class KeyboardReader:

        def __init__(self, ship):
            self.__ship = ship

        def readline(self):
            return self.__ship.readKeyboard() + '\n'

    def __init__(self):
        self.__device = Device()
        self.__sensor_devices = {}
        self.__interface_devices = {}
        self.__engine_devices = {}
        self.__console_printer = Ship.ConsolePrinter(self)
        self.__keyboard_reader = Ship.KeyboardReader(self)

        self.__find_devices(self.__device)

        console = self.__interface_devices.get('console-text-display')
        if console:
            self.__main_console = console[0]
        else:
            self.__main_console = None

        keyboard = self.__interface_devices.get('keyboard')
        if keyboard:
            self.__main_keyboard = keyboard[0]
        else:
            self.__main_keyboard = None

    def run(self, seconds):
        start_time = time.time()

        if self.__main_console is not None:
            self.__main_console.flush()

        time.sleep(max(seconds - (time.time() - start_time), 0))

    def listInterfaceDevices(self, device_type=None):
        if device_type is None:
            return self.__interface_devices

        return self.__interface_devices.get(device_type, ())

    def listEngines(self, engine_type=None):
        if engine_type is None:
            return self.__engine_devices

        return self.__engine_devices.get(engine_type, ())

    def listSensors(self, sensor_type=None):
        if sensor_type is None:
            return self.__sensor_devices

        return self.__sensor_devices.get(sensor_type, ())

    @property
    def console_printer(self):
        return self.__console_printer

    @property
    def keyboard_reader(self):
        return self.__keyboard_reader

    def writeConsole(self, text):
        self.__main_console.write(text)

    def readKeyboard(self):
        return self.__main_keyboard.readline()

    def displayPrint(self, message):

        text_displays = self.__interface_devices.get('text-display')
        if text_displays:
            text_displays[0].sendMessage(f'set-text "{message}"')

    @property
    def position(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('position-sensor')

        if not position_devices:
            return None

        device = position_devices[0]

        return (device.read('x'), device.read('y'))

    @property
    def angle(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('angle-sensor')

        if not position_devices:
            return None

        device = position_devices[0]

        return float(device.read())

    @property
    def speed(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('speed-sensor')

        if not position_devices:
            return None

        device = position_devices[0]

        return device.read()

    @property
    def angular_speed(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('ang-speed-sensor')

        if not position_devices:
            return None

        device = position_devices[0]

        return device.read()

    @property
    def device(self):
        return self.__device

    def __find_devices(self, device):

        if isinstance(device, Sensor):

            devices = self.__sensor_devices.get(device.type_)
            if devices is None:
                self.__sensor_devices[device.type_] = [device]
            else:
                devices.append(device)
            return

        if device.type_ in ('text-display', 'console-text-display',
                            'keyboard'):
            devices = self.__interface_devices.get(device.type_)
            if devices is None:
                self.__interface_devices[device.type_] = [device]
            else:
                devices.append(device)
            return

        if isinstance(device, Engine):
            devices = self.__engine_devices.get(device.type_)
            if devices is None:
                self.__engine_devices[device.type_] = [device]
            else:
                devices.append(device)
            return

        children = device.children
        if children is None:
            return

        for child in device.children:
            self.__find_devices(child)

def send(message):

    __device_comm_write.write(message)
    __device_comm_write.write('\n')
    __device_comm_write.flush()

    return __device_comm_read.readline()[:-1]

def debug(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
    sys.stderr.flush()

ship = Ship()

sys.stdout = ship.console_printer
sys.stdin = ship.keyboard_reader
