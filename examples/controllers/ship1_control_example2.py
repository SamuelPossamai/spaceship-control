#!/usr/bin/env python3

import sys
from lib.programargs import program_args_info
from lib.spctrl_base_controller import ship, send, debug
from lib.console_interface import ConsoleInterface

output_device = ship.listInterfaceDevices('console-text-display')[0]
input_device = ship.listInterfaceDevices('keyboard')[0]

console = ConsoleInterface(ship, input_device, output_device)

input_device.sendMessage('activate')

while True:
    try:
        pass
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    console.run()
    ship.run(.1)
