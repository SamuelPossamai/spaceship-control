#!/usr/bin/env python3

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

engines = ship.listEngines('linear-engine')
dist_sensors = ship.listSensors('line-dist-sensor')
speed_sensor = ship.listSensors('speed-sensor')[0]
angular_speed_sensor = ship.listSensors('ang-speed-sensor')[0]

while True:
    try:
        speed = speed_sensor.read()
        angular_speed = angular_speed_sensor.read()

        dist_values = tuple(sensor.read() for sensor in dist_sensors)

        debug(int(speed), int(angular_speed),
              tuple(int(val) for val in dist_values))

        if dist_values[2] < 800:
            engines[0].intensity = 1
            engines[1].intensity = 0
        else:
            intensity = 4/(1 + speed/100)

            engines[0].intensity = intensity
            engines[1].intensity = intensity

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
