
from collections import namedtuple
from typing import TYPE_CHECKING, cast as typingcast

from pymunk import Body

from ...devices.structure import Structure, StructuralPart

from .shapeloader import ShapeLoader
from .imageloader import loadImages
from .deviceloader import DeviceLoader

if TYPE_CHECKING:
    from typing import (
        Tuple, Sequence, Any, MutableMapping, List, Callable, Optional
    )
    import pymunk
    from PyQt5.QtWidgets import QWidget
    from ...devices.device import Device
    from ...devices.communicationdevices import CommunicationEngine

    CreateDeviceCallable = Callable[..., Tuple[Device, Sequence[QWidget]]]

    DeviceKindType = Tuple[Optional[str], Optional[str], Optional[str]]
    DeviceCreateFunctionsType = MutableMapping[DeviceKindType,
                                               CreateDeviceCallable]

ShipInfo = namedtuple('ShipInfo', ('device', 'images', 'widgets'))

def loadShip(ship_info: 'MutableMapping[str, Any]', name: str,
             space: 'pymunk.Space', prefixes: 'Sequence[str]' = (),
             communication_engine: 'Optional[CommunicationEngine]' = None,
             shape_loader=None) \
        -> 'ShipInfo':

    return ShipLoader(shape_loader=shape_loader).load(
        ship_info, name, space, prefixes=prefixes,
        communication_engine=communication_engine,)

class ShipLoader:

    def __init__(self, shape_loader=None) -> None:
        self.__device_loader = DeviceLoader()
        if shape_loader is None:
            self.__shape_loader = ShapeLoader()
        else:
            self.__shape_loader = shape_loader

    def load(self, ship_info: 'MutableMapping[str, Any]', name: str,
             space: 'pymunk.Space', prefixes: 'Sequence[str]' = (),
             communication_engine: 'Optional[CommunicationEngine]' = None) \
        -> 'ShipInfo':

        shapes = self.__shape_loader.load(ship_info['Shape'])

        mass = sum(shape.mass for shape in shapes)
        moment = sum(shape.moment for shape in shapes)

        if mass <= 0:
            raise Exception(f"Ship \'{name}\' has invalid mass")

        body = Body(mass, moment)

        for shape in shapes:
            shape.body = body

        space.add(body, shapes)

        ship, parts = self.__loadShipStructure(ship_info, name, space, body)

        for info in ship_info.get('Actuator', ()):
            self.__addDevice(info, parts, 'Actuator')

        for info in ship_info.get('Sensor', ()):
            self.__addDevice(info, parts, 'Sensor')

        for info in ship_info.get('Communication', ()):
            self.__addDevice(info, parts, 'Communication',
                             engine=communication_engine)

        widgets: 'List[QWidget]' = []
        for info in ship_info.get('InterfaceDevice', ()):
            widgets.extend(
                self.__addDevice(info, parts, 'InterfaceDevice'))

        return ShipInfo(device=ship, images=loadImages(
            ship_info.get('Image', ()), prefixes=prefixes), widgets=widgets)

    def __addDevice(
            self, info: 'MutableMapping[str, Any]',
            parts: 'MutableMapping[str, StructuralPart]',
            device_type: str, **kwargs: 'Any') -> 'Sequence[QWidget]':

        part_name = typingcast(str, info.get('part'))
        part = parts.get(part_name)

        if part is None:
            raise Exception(f"{device_type} has invalid part \'{part_name}\'.")

        return self.__device_loader.load(device_type, info, part, **kwargs)[1]

    def __loadShipStructure(
            self, ship_info: 'MutableMapping[str, Any]', name: str,
            space: 'pymunk.Space', body: 'pymunk.Body') \
                -> 'Tuple[Structure, MutableMapping[str, StructuralPart]]':

        ship = Structure(name, space, body, device_type='ship')

        parts = {}
        for part_info in ship_info.get('Part', ()):
            part_name = str(part_info.get('name', 'unnamed'))
            part = StructuralPart(offset=(part_info['x'], part_info['y']))

            ship.addDevice(part, name=part_name)
            parts[part_name] = part

        return ship, parts
