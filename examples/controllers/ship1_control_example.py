
import time
import sys

import collections

__device_comm_write = sys.__stdout__
__device_comm_read = sys.__stdin__

sys.stdout = sys.stderr
sys.stdin = None

class Device:

    def __init__(self, device_path=''):

        self.__device_path = device_path

        if self.sendMessage('get-info is-device-group') == 'yes':

            children_count = int(self.sendMessage('device-count'))

            if device_path == '':
                dev_path_prefix = ':'
            else:
                dev_path_prefix = device_path

            self.__children = tuple(Device(device_path=f'{device_path}{i}:')
                                    for i in range(children_count))
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

SensorInfo = collections.namedtuple('SensorInfo', ('reading_time',
                                                    'max_error',
                                                    'max_offset',
                                                    'estimated_offset'))

class Ship:

    def __init__(self):
        self.__device = Device()
        self.__sensor_devices = {}
        self.__text_display_devices = []
        self.__find_position_devices(self.__device)

    def displayPrint(self, message):

        if self.__text_display_devices:
            self.__text_display_devices[0].sendMessage(f'set-text "{message}"')

    @property
    def position(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('position-sensor')

        if not position_devices:
            return None

        device = position_devices[0][0]

        return (float(device.sendMessage('x:read')),
                float(device.sendMessage('y:read')))

    @property
    def angle(self):
        if not self.__sensor_devices:
            return None

        position_devices = self.__sensor_devices.get('angle-sensor')

        if not position_devices:
            return None

        device = position_devices[0][0]

        return float(device.sendMessage('read'))

    @property
    def device(self):
        return self.__device

    def __find_position_devices(self, device):

        if device.type_ in ('position-sensor', 'angle-sensor'):
            reading_time = float(device.sendMessage('reading-time'))
            max_offset = float(device.sendMessage('max-offset'))
            max_error = float(device.sendMessage('max-error')) - max_offset
            info = SensorInfo(reading_time=reading_time,
                              max_error=max_error,
                              max_offset=max_offset,
                              estimated_offset=0)

            sensor_info = (device, info)

            devices = self.__sensor_devices.get(device.type_)
            if devices is None:
                self.__sensor_devices[device.type_] = [sensor_info]
            else:
                devices.append(sensor_info)
            return

        if device.type_ == 'text-display':
            self.__text_display_devices.append(device)
            return

        children = device.children
        if children is None:
            return

        for child in device.children:
            self.__find_position_devices(child)

def send(message):

    __device_comm_write.write(message)
    __device_comm_write.write('\n')
    __device_comm_write.flush()

    return __device_comm_read.readline()[:-1]

ship = Ship()

print(ship.device)

colors = ('black', 'red', 'blue', 'green')
color_id = 0

send('1:5: set-cursor-pos 3 1')
send('1:5: write "Spaceship Control"')
send('1:5: set-cursor-pos 1 5')
send('1:5: write "This is just an example controller"')
send('1:5: update')

while True:
    try:
        if send('1:3: clicked') == '1':
            color_id += 1
            if color_id >= len(colors):
                color_id = 0

        print(send('1:4: get'))

        print('Speed:', send('0:3: read'))

        pos = ship.position
        angle = ship.angle
        intensity = -(pos[0] - 500) // 100
        send(f'0:0: set-property intensity {intensity}')
        print(pos, intensity)
        ship.displayPrint(f'<font color={colors[color_id]}>{pos[0]:.1f}, '
                          f'{pos[1]:.1f} ({angle:.1f}º)</font>')

    except BrokenPipeError:
        break
    except Exception as err:
        print(f'Error: {err}')
    time.sleep(1)