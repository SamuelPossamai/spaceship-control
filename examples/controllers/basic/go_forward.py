#!/usr/bin/env python3

import sys

from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

from lib.programargs import program_args_info
from lib.spctrl_base_controller import ship, send, debug

sys.__stderr__.flush()

debug(program_args_info)

send('0:0: set-property intensity 1')
while True:
    try:
        debug(ship.position)
        ship.run(.25)
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')
