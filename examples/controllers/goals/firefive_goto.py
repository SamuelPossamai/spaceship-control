#!/usr/bin/env python3

import sys
import math

from pathlib import Path

import random
import json

sys.path.append(str(Path(__file__).parents[1]))

from lib.spctrl_base_controller import ship, send, debug

def getAngleDiff(ang1, ang2):

    angle_diff = ang1 - ang2
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    return angle_diff

debug(ship.device)

args_info = json.loads(sys.argv[1])

goto_objectives = (objective_info.get('info') for objective_info in
                   args_info.get('objectives', ())
                   if objective_info.get('type') == 'GoToObjective')

goto_objectives = [(objective_info.get('target-x'),
                   objective_info.get('target-y'))
                   for objective_info in goto_objectives]

engines = ship.listEngines('linear-engine')

target = goto_objectives[0]
del goto_objectives[0]

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

        angle_diff = getAngleDiff(desired_angle, angle)

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
        elif angle_diff_abs < 3 and angular_speed_abs < 1:
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

            if not goto_objectives:
                engines[0].intensity = 4
                engines[1].intensity = 4
                engines[2].intensity = 4
                engines[3].intensity = 4
                engines[4].intensity = 4
                sys.exit()

            target_weight = math.inf
            target_index = -1
            for i, cur_target in enumerate(goto_objectives):
                distance = math.sqrt((cur_target[1] - position[1])**2 +
                                     (cur_target[0] - position[0])**2)
                angle_diff = getAngleDiff(
                    180*math.atan2(cur_target[1] - position[1],
                                   cur_target[0] - position[0])/math.pi, angle)

                current_target_weight = distance*angle_diff**2
                if target_weight > current_target_weight:
                    target_weight = current_target_weight
                    target_index = i

            target = goto_objectives[target_index]
            del goto_objectives[target_index]

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
