#!/usr/bin/env python3

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

print('\n   Spaceship Control')
print('\n\n This is just an example controller')

engines = ship.listEngines('linear-engine')

while True:
    try:

        engines[0].intensity = 4
        engines[1].intensity = 4

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(.1)
