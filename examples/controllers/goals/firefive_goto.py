#!/usr/bin/env python3

import sys

from pathlib import Path

import random

sys.path.append(str(Path(__file__).parents[1]))

from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

engines = ship.listEngines('linear-engine')
speed_sensor = ship.listSensors('speed-sensor')[0]
angular_speed_sensor = ship.listSensors('ang-speed-sensor')[0]

for engine in engines:
    engine.intensity = 4

current_engine = 0

while True:
    try:
        speed = speed_sensor.read()
        angular_speed = angular_speed_sensor.read()

        debug(int(speed), int(angular_speed))

        engines[current_engine].intensity = 4*random.random()

        current_engine = (current_engine + 1) % len(engines)

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
