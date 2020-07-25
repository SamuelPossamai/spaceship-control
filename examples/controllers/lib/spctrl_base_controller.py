#!/usr/bin/env python3

import sys
import time

import collections

__device_comm_write = sys.__stdout__
__device_comm_read = sys.__stdin__

class Device:

    _DEVICE_TYPE_MAP = {}

    def __init__(self, device_path=''):

        self.__device_path = device_path

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
                children.append(child_class(device_path=f'{device_path}{i}:'))

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

SensorInfo = collections.namedtuple('SensorInfo', (
    'reading_time', 'max_error', 'max_offset', 'estimated_offset'))

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
        self.__message_buffer = ''

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

    def __printMsg(self, text):
        self.__main_console.sendMessage(f'write "{text}"')

    def run(self, seconds):
        start_time = time.time()

        if self.__main_console is not None:

            self.__message_buffer = \
                self.__message_buffer.replace("'", "\\'").replace('\\', '\\\\')

            messages = iter(self.__message_buffer.split('\n'))

            self.__printMsg(next(messages))
            for message in messages:
                self.__main_console.sendMessage('LF')
                if message:
                    self.__printMsg(message)

            self.__main_console.sendMessage('update')
            self.__message_buffer = ''

        time.sleep(max(seconds - (time.time() - start_time), 0))

    def listEngines(self, engine_type=None):
        if engine_type is None:
            return self.__engine_devices

        return self.__engine_devices.get(engine_type, ())

    @property
    def console_printer(self):
        return self.__console_printer

    @property
    def keyboard_reader(self):
        return self.__keyboard_reader

    def writeConsole(self, text):
        self.__message_buffer += text

    def readKeyboard(self):
        return self.__main_keyboard.sendMessage('get')

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
                devices.append(sensor_info)
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
