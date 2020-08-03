#!/usr/bin/env python3

import sys
import math

from pathlib import Path

import random
import json

sys.path.append(str(Path(__file__).parents[1]))

from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

args_info = json.loads(sys.argv[1])

goto_objectives = (objective_info.get('info') for objective_info in
                   args_info.get('objectives', ())
                   if objective_info.get('type') == 'GoToObjective')

goto_objectives = [(objective_info.get('target-x'),
                   objective_info.get('target-y'))
                   for objective_info in goto_objectives]

debug(goto_objectives)

engines = ship.listEngines('linear-engine')

for engine in engines:
    engine.intensity = 4

current_engine = 0

objectives_iter = iter(goto_objectives)
target = next(objectives_iter)

while True:
    try:
        debug(target)

        position = ship.position
        angle = ship.angle
        speed = ship.speed
        angular_speed = ship.angular_speed

        debug(int(speed), int(angular_speed), position, angle)

        engines[current_engine].intensity = 4*random.random()

        current_engine = (current_engine + 1) % len(engines)

        if math.isclose(position[0], target[0], rel_tol=0, abs_tol=10) and \
            math.isclose(position[1], target[1], rel_tol=0, abs_tol=10):

            target = next(objectives_iter)

            if target is None:
                sys.exit()

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
