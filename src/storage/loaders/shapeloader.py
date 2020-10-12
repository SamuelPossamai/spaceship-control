
from typing import TYPE_CHECKING

from pymunk import Shape, Circle, Poly, Segment

from .customloader import CustomLoader

if TYPE_CHECKING:
    from typing import Any, Dict, Sequence, Tuple
    import pymunk

def loadShapes(info_list: 'Sequence[Dict[str, Any]]') \
    -> 'Tuple[pymunk.Shape, ...]':

    return ShapeLoader().load(info_list)

class ShapeLoader(CustomLoader):

    def __init__(self):
        super().__init__(self.__SHAPE_CREATE_FUNCTIONS, label='Shape')

    def _addCustom(self, config, model_type, model_info):
        pass

    def load(self, info_list: 'Sequence[Dict[str, Any]]') \
            -> 'Tuple[pymunk.Shape, ...]':

        shapes = []

        for shape_info in info_list:
            new_shapes = self.__createShape(shape_info)
            if new_shapes is not None:
                if isinstance(new_shapes, Shape):
                    shapes.append(new_shapes)
                else:
                    shapes.extend(new_shapes)

        return tuple(shapes)

    def __createShape(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        type_ = info.get('type')

        create_func = self._load_functions.get(type_)

        if create_func is None:
            raise Exception(f'Invalid shape type \'{type_}\'')

        return create_func(self, info)

    @staticmethod
    def __setGeneralProperties(shape: 'pymunk.Shape',
                               info: 'Dict[str, Any]') -> None:

        shape.mass = info.get('mass', 0)
        shape.elasticity = info.get('elasticity', 0.5)
        shape.friction = info.get('friction', 0.5)

    def __createCircleShape(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        shape = Circle(None, info['radius'],
                    (info.get('x', 0), info.get('y', 0)))

        self.__setGeneralProperties(shape, info)

        return shape

    def __createPolyShape(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        points = tuple((point.get('x', 0), point.get('y', 0))
                    for point in info['Point'])
        shape = Poly(None, points)

        self.__setGeneralProperties(shape, info)

        return shape

    def __createRectangleShape(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        pos_x = info.get('x')
        pos_y = info.get('y')

        if pos_x is None or pos_y is None:
            raise ValueError('Both \'x\' and \'y\' position of a rectangle '
                            'shape must be provided')

        width = info.get('width')
        height = info.get('height')

        if width is None or height is None:
            raise ValueError('Both \'width\' and \'height\' of a rectangle '
                            'shape must be provided')

        shape = Poly(None, (
            (pos_x, pos_y), (pos_x + width, pos_y),
            (pos_x + width, pos_y + height), (pos_x, pos_y + height)))

        self.__setGeneralProperties(shape, info)

        return shape

    def __createLineShape(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        points = info.get('Point', ())

        if len(points) != 2:
            raise ValueError('Line must have exactly two points')

        points = tuple((point.get('x', 0), point.get('y', 0))
                    for point in points)

        if points[0] == points[1]:
            raise ValueError('Start and end of the line must be different')

        thickness = info.get('thickness', 1)
        if thickness <= 0:
            raise ValueError('Line thickness must be greater than 0')

        shape = Segment(None, points[0], points[1], info.get('thickness', 1))

        self.__setGeneralProperties(shape, info)

        return shape

    def __createShapeGroup(self, info: 'Dict[str, Any]') -> 'pymunk.Shape':

        shapes_info = info.get('Shape')

        if shapes_info:
            return self.load(shapes_info)

        return None

    __SHAPE_CREATE_FUNCTIONS = {

        'circle': __createCircleShape,
        'polygon': __createPolyShape,
        'line': __createLineShape,
        'rectangle': __createRectangleShape,
        'group': __createShapeGroup
    }
