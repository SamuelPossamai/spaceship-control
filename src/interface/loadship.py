
import json
import math

try:
    from queue import SimpleQueue
except ImportError:
    from queue import Queue as SimpleQueue

import anytree

from .loadgraphicitem import loadGraphicItem

from ..storage.fileinfo import FileInfo

def loadShip(space, ship_info, arg_scenario_info, lock,
             ship_options_dialog=None, controller_options_dialog=None,
             communication_engine=None):

    fileinfo = FileInfo()

    arg_scenario_info['ship-name'] = ship_info.name
    arg_scenario_info['starting-position'] = ship_info.position
    arg_scenario_info['starting-angle'] = 180*ship_info.angle/math.pi

    json_info = json.dumps(arg_scenario_info)

    ship_model = ship_info.model
    ship_model_is_tuple = isinstance(ship_model, tuple)

    if ship_model_is_tuple or ship_model is None:
        if ship_model_is_tuple:
            ship_options = tuple(anytree.Node(model_option)
                                    for model_option in ship_model)
        else:
            ship_options = fileinfo.listFilesTree(
                FileInfo.FileDataType.SHIPMODEL).children

        if ship_options_dialog is not None:
            ship_model = ship_options_dialog(ship_options)

        if ship_model is None:
            return None

        ship_model = '/'.join(ship_model)

    loaded_ship = fileinfo.loadShip(
        ship_model, ship_info.name, space,
        communication_engine=communication_engine,
        variables=ship_info.variables)

    ship = loaded_ship.device

    widgets = loaded_ship.widgets
    ship.body.position = ship_info.position
    ship.body.angle = ship_info.angle

    ship_controller = ship_info.controller

    if ship_controller is None:

        controller_options = fileinfo.listFilesTree(
            FileInfo.FileDataType.CONTROLLER).children

        if controller_options_dialog is not None:
            ship_controller = controller_options_dialog(controller_options)

        if ship_controller is None:
            return None

        ship_controller = '/'.join(ship_controller)

    msg_queue = SimpleQueue()
    thread = fileinfo.loadController(ship_controller, ship, json_info,
                                     msg_queue, lock)

    ship_gitem, condition_graphic_items = loadGraphicItem(
        ship.body.shapes, loaded_ship.images,
        condition_variables={'ship': ship.mirror})

    return ship, ship_gitem, widgets, thread, msg_queue, condition_graphic_items
