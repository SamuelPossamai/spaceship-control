
from collections import namedtuple
import json
import math
from typing import TYPE_CHECKING

try:
    from queue import SimpleQueue
except ImportError:
    from queue import Queue as SimpleQueue # type: ignore

import anytree

from .loadgraphicitem import loadGraphicItem

from ..storage.fileinfo import FileInfo

if TYPE_CHECKING:
    from threading import Lock
    from typing import Optional, Dict, Any, Callable, Sequence
    import pymunk
    from anytree import Node
    from ..devices.communicationdevices import CommunicationEngine
    from ..storage.loaders.scenarioloader import ShipInfo

    DialogCallable = Callable[[Node], Optional[Sequence[str]]]

ShipInterfaceInfo = namedtuple('ShipInfo', (
    'device', 'gitem', 'widgets', 'thread',
    'msg_queue', 'condition_graphic_items'))

def __loadShipSelectModel(ship_model: 'Optional[Sequence[str]]',
                          options_dialog: 'Optional[DialogCallable]') \
                              -> 'Optional[str]':

    if ship_model is not None:
        ship_options = tuple(anytree.Node(model_option)
                             for model_option in ship_model)
    else:
        options_tree = FileInfo().listFilesTree(
            FileInfo.FileDataType.CONTROLLER)
        if options_tree is None:
            return None

        ship_options = options_tree.children

    if options_dialog is not None:
        ship_model = options_dialog(ship_options)

    if ship_model is None:
        return None

    return '/'.join(ship_model)

def __loadShipSelectController(options_dialog: 'Optional[DialogCallable]') \
        -> 'Optional[str]':

    options_tree = FileInfo().listFilesTree(FileInfo.FileDataType.CONTROLLER)
    if options_tree is None:
        return None

    controller_options = options_tree.children

    if options_dialog is not None:
        ship_controller = options_dialog(controller_options)

    if ship_controller is None:
        return None

    return '/'.join(ship_controller)

def loadShip(space: 'pymunk.Space', ship_info: 'ShipInfo',
             arg_scenario_info: 'Dict[str, Any]', lock: 'Lock',
             ship_options_dialog: 'DialogCallable' = None,
             controller_options_dialog: 'DialogCallable' = None,
             communication_engine: 'CommunicationEngine' = None) \
                 -> 'Optional[ShipInterfaceInfo]':

    arg_scenario_info['ship-name'] = ship_info.name
    arg_scenario_info['starting-position'] = ship_info.position
    arg_scenario_info['starting-angle'] = 180*ship_info.angle/math.pi

    ship_model = ship_info.model

    if isinstance(ship_model, tuple) or ship_model is None:
        ship_model = __loadShipSelectModel(ship_model, ship_options_dialog)
        if ship_model is None:
            return None

    loaded_ship = FileInfo().loadShip(
        ship_model, ship_info.name, space,
        communication_engine=communication_engine,
        variables=ship_info.variables)

    ship = loaded_ship.device

    ship.body.position = ship_info.position
    ship.body.angle = ship_info.angle

    ship_controller = ship_info.controller

    if ship_controller is None:
        ship_controller = __loadShipSelectController(controller_options_dialog)
        if ship_controller is None:
            return None

    msg_queue: 'SimpleQueue' = SimpleQueue()
    thread = FileInfo().loadController(ship_controller, ship,
                                       json.dumps(arg_scenario_info),
                                       msg_queue, lock)

    ship_gitem, condition_graphic_items = loadGraphicItem(
        ship.body.shapes, loaded_ship.images,
        condition_variables={'ship': ship.mirror})

    return ShipInterfaceInfo(ship, ship_gitem, loaded_ship.widgets,
                             thread, msg_queue,
                             condition_graphic_items)
