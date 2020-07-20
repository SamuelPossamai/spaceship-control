#!/usr/bin/env python3

import sys
from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

colors = ('black', 'red', 'blue', 'green')
color_id = 0

debug(sys.argv[1:])

print('\n   Spaceship Control')
print('\n\n This is just an example controller')

while True:
    try:
        if send('1:2: clicked') == '1':
            color_id += 1
            if color_id >= len(colors):
                color_id = 0

        commands_str = input()
        commands = []
        for i in range(10, len(commands_str) + 1, 10):
            commands.append(commands_str[i - 10: i])

        if '0001000013' in commands:
            engine_one_intensity = 4
        else:
            engine_one_intensity = 0

        if '0001000015' in commands:
            engine_one_intensity -= 4

        if '0001000012' in commands:
            engine_two_intensity = 4
        else:
            engine_two_intensity = 0

        if '0001000014' in commands:
            engine_three_intensity = 4
        else:
            engine_three_intensity = 0

        debug(commands)

        debug('Speed:', send('0:3: read'))

        pos = ship.position
        angle = ship.angle
        debug(pos, engine_one_intensity)
        ship.displayPrint(f'<font color={colors[color_id]}>{pos[0]:.1f}, '
                          f'{pos[1]:.1f} ({angle:.1f}º)</font>')

        send(f'0:0: set-property intensity {engine_one_intensity}')
        send(f'1:0: set-property intensity {engine_two_intensity}')
        send(f'2:0: set-property intensity {engine_three_intensity}')

        debug('Distance: ', send(f'0:4: read'))

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
