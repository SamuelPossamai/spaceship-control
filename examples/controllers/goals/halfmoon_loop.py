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

while True:
    try:
        speed = speed_sensor.read()

        dist_values = tuple(sensor.read() for sensor in dist_sensors)

        debug(int(speed), tuple(int(val) for val in dist_values))

        if dist_values[2] < 800:
            engines[0].intensity = 1
            engines[1].intensity = 0
        else:
            engines[0].intensity = 4
            engines[1].intensity = 4

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
