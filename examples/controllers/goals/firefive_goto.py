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

objectives_iter = iter(goto_objectives)
target = next(objectives_iter)

while True:
    try:
        debug(target)

        position = ship.position
        angle = ship.angle % 360
        speed = ship.speed
        angular_speed = ship.angular_speed

        debug(int(speed), int(angular_speed), position, angle)

        desired_angle = 180*math.atan2(target[1] - position[1],
                                       target[0] - position[0])/math.pi

        angle_diff = desired_angle - angle
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        angle_diff_abs = abs(angle_diff)
        angular_speed_abs = abs(angular_speed)

        if angular_speed_abs > 4*angle_diff_abs:

            if angular_speed_abs > 75:
                intensity = 4
            else:
                intensity = angular_speed_abs//25 + 1

            engines[0].intensity = 0
            if angular_speed > 0:
                engines[1].intensity = 0
                engines[2].intensity = 0
                engines[3].intensity = intensity
                engines[4].intensity = intensity
            else:
                engines[1].intensity = intensity
                engines[2].intensity = intensity
                engines[3].intensity = 0
                engines[4].intensity = 0
        elif angle_diff_abs < 5 and angular_speed < 1:
            engines[0].intensity = 4
            engines[1].intensity = 4
            engines[2].intensity = 4
            engines[3].intensity = 4
            engines[4].intensity = 4
        else:
            engines[0].intensity = 0
            if angle_diff > 0:
                engines[1].intensity = 1
                engines[2].intensity = 4
                engines[3].intensity = 0
                engines[4].intensity = 0
            else:
                engines[1].intensity = 0
                engines[2].intensity = 0
                engines[3].intensity = 1
                engines[4].intensity = 4

        if angle_diff_abs > 60:
            engines[0].intensity = 4

        if math.isclose(position[0], target[0], rel_tol=0, abs_tol=30) and \
            math.isclose(position[1], target[1], rel_tol=0, abs_tol=30):

            target = next(objectives_iter)

            if target is None:
                sys.exit()

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
