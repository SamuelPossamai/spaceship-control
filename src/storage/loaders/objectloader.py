
from collections import namedtuple
from typing import TYPE_CHECKING

from pymunk import Body

from .shapeloader import loadShapes
from .imageloader import loadImages

ObjectInfo = namedtuple('ObjectInfo', ('body', 'images'))

if TYPE_CHECKING:
    from typing import Tuple, Sequence, Any, MutableMapping
    import pymunk
    from PyQt5.QtWidgets import QWidget
    from ...devices.structure import Structure

def loadObject(obj_info: 'MutableMapping[str, Any]', space: 'pymunk.Space',
               prefixes: 'Sequence[str]' = ()) -> 'ObjectInfo':

    config_content = obj_info.get('Config', {})

    if config_content is None:
        is_static = False
    else:
        is_static = config_content.get('static', False)

    shapes = loadShapes(obj_info['Shape'])

    if is_static is True:

        body = Body(body_type=Body.STATIC)

        for shape in shapes:
            shape.body = body

        space.add(shapes)

    else:
        mass = sum(shape.mass for shape in shapes)
        moment = sum(shape.moment for shape in shapes)

        body = Body(mass, moment)

        for shape in shapes:
            shape.body = body

        space.add(body, shapes)

    return ObjectInfo(body, loadImages(obj_info.get('Image', ()),
                                       prefixes=prefixes))
