
import functools
from typing import TYPE_CHECKING

from pymunk import Shape, Circle, Poly, Segment

from .customloader import CustomLoader

from .. import configfilevariables

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

        mode = config.get('mode')
        if mode == 'static':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicShapeFunction, model_info)
        elif mode is None or mode == 'dynamic':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicShapeFunction, model_info)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    @staticmethod
    def __createCustomStaticShapeFunction(
            shape_content: 'MutableMapping[str, Any]', loader,
            custom_shape_info: 'MutableMapping[str, Any]',
            default_elasticity: float = None,
            default_friction: float = None):

        return loader.load((shape_content,),
                           default_elasticity=default_elasticity,
                           default_friction=default_friction)

    @staticmethod
    def __createCustomDynamicShapeFunction(
            shape_content: 'MutableMapping[str, Any]', loader,
            custom_shape_info: 'MutableMapping[str, Any]',
            default_elasticity: float = None,
            default_friction: float = None):

        variables = {variable['id']: variable['value'] for variable in
                     shape_content.get('Variable', ())}

        configfilevariables.subVariables(shape_content,
                                         variables=variables,
                                         enabled=True)

        return loader.load((shape_content,),
                           default_elasticity=default_elasticity,
                           default_friction=default_friction)

    def load(self, info_list: 'Sequence[Dict[str, Any]]',
             default_elasticity: float = None,
             default_friction: float = None) \
            -> 'Tuple[pymunk.Shape, ...]':

        shapes = []

        for shape_info in info_list:
            new_shapes = self.__createShape(
                shape_info, default_elasticity=default_elasticity,
                default_friction=default_friction)
            if new_shapes is not None:
                if isinstance(new_shapes, Shape):
                    shapes.append(new_shapes)
                else:
                    shapes.extend(new_shapes)

        return tuple(shapes)

    def __createShape(self, info: 'Dict[str, Any]',
                      default_elasticity: float = None,
                      default_friction: float = None) -> 'pymunk.Shape':

        type_ = info.get('type')

        create_func = self._load_functions.get(type_)

        if create_func is None:
            raise Exception(f'Invalid shape type \'{type_}\'')

        return create_func(self, info, default_elasticity=default_elasticity,
                           default_friction=default_friction)

    @staticmethod
    def __setGeneralProperties(shape: 'pymunk.Shape',
                               info: 'Dict[str, Any]',
                               default_elasticity: float = None,
                               default_friction: float = None) -> None:

        if default_elasticity is None:
            default_elasticity = 0.5

        if default_friction is None:
            default_friction = 0.5

        shape.mass = info.get('mass', 0)
        shape.elasticity = info.get('elasticity', default_elasticity)
        shape.friction = info.get('friction', default_friction)

        print(shape.elasticity)

    def __createCircleShape(self, info: 'Dict[str, Any]',
                            default_elasticity: float = None,
                            default_friction: float = None) -> 'pymunk.Shape':

        shape = Circle(None, info['radius'],
                       (info.get('x', 0), info.get('y', 0)))

        self.__setGeneralProperties(shape, info,
                                    default_elasticity=default_elasticity,
                                    default_friction=default_friction)

        return shape

    def __createPolyShape(self, info: 'Dict[str, Any]',
                          default_elasticity: float = None,
                          default_friction: float = None) -> 'pymunk.Shape':

        points = tuple((point.get('x', 0), point.get('y', 0))
                       for point in info['Point'])
        shape = Poly(None, points)

        self.__setGeneralProperties(shape, info,
                                    default_elasticity=default_elasticity,
                                    default_friction=default_friction)

        return shape

    def __createRectangleShape(self, info: 'Dict[str, Any]',
                               default_elasticity: float = None,
                               default_friction: float = None) \
                                   -> 'pymunk.Shape':

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

        self.__setGeneralProperties(shape, info,
                                    default_elasticity=default_elasticity,
                                    default_friction=default_friction)

        return shape

    def __createLineShape(self, info: 'Dict[str, Any]',
                          default_elasticity: float = None,
                          default_friction: float = None) -> 'pymunk.Shape':

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

        self.__setGeneralProperties(shape, info,
                                    default_elasticity=default_elasticity,
                                    default_friction=default_friction)

        return shape

    def __createShapeGroup(self, info: 'Dict[str, Any]',
                          default_elasticity: float = None,
                          default_friction: float = None) -> 'pymunk.Shape':

        shapes_info = info.get('Shape')

        if shapes_info:

            default_elasticity = info.get(
                'elasticity', default_elasticity)

            default_friction = info.get('friction', default_friction)

            return self.load(shapes_info,
                             default_elasticity=default_elasticity,
                             default_friction=default_friction)

        return None

    __SHAPE_CREATE_FUNCTIONS = {

        'circle': __createCircleShape,
        'polygon': __createPolyShape,
        'line': __createLineShape,
        'rectangle': __createRectangleShape,
        'group': __createShapeGroup
    }
