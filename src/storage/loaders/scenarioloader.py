
from math import pi
from collections import namedtuple
from typing import TYPE_CHECKING

from .imageloader import loadImages
from .objectiveloader import loadObjectives

from ..configfileinheritance import resolvePrefix

from ...devices.communicationdevices import CommunicationEngine

if TYPE_CHECKING:
    from typing import Any, MutableMapping, Optional, Sequence
    from ...objectives.objective import Objective

ObjectInfo = namedtuple('ObjectInfo', (
    'model', 'position', 'angle', 'variables'))

ShipInfo = namedtuple('ShipInfo', (
    'name', 'model', 'controller', 'position', 'angle', 'variables'))

PhysicsEngineInfo = namedtuple('PhysicsEngineInfo',
                               ('damping', 'gravity', 'collision_slop',
                                'collision_persistence', 'iterations'))

ScenarioInfo = namedtuple('ScenarioInfo', (
    'name', 'ships', 'objectives', 'objects', 'visible_user_interface',
    'communication_engine', 'visible_debug_window', 'static_images',
    'physics_engine'
))

def __resolveShipModelPrefix(model: str, prefixes: 'Sequence[str]') -> str:

    model_after, _ = resolvePrefix(model, prefixes)

    if model_after is None:
        raise ValueError(f'Ship model not found \'{model}\'')

    return model_after

def __readShipInfo(ship_content: 'MutableMapping[str, Any]',
                   prefixes: 'Sequence[str]') -> 'ShipInfo':

    model_metadata = ship_content.get('__model_attr_meta__')
    if model_metadata is not None:
        prefixes = model_metadata.get('parentpath', prefixes)

    model = ship_content.get('model')
    if model is not None:
        if isinstance(model, list):
            model = tuple(__resolveShipModelPrefix(single_model, prefixes)
                          for single_model in model)
        else:
            model = __resolveShipModelPrefix(model, prefixes)

    controller = ship_content.get('controller')

    if controller is not None:
        controller, _ = resolvePrefix(controller, prefixes)

    variables_content = ship_content.get('Variable')

    variables: 'Optional[MutableMapping[str, Any]]'
    if variables_content:
        variables = {variable['id']: variable['value']
                     for variable in variables_content}
    else:
        variables = None

    ship_info_kwargs = {

        'name': ship_content.get('name', '<<nameless>>'),
        'controller': controller,
        'model': model,
        'position': (ship_content.get('x', 0), ship_content.get('y', 0)),
        'angle': pi*ship_content.get('angle', 0)/180,
        'variables': variables
    }

    return ShipInfo(**ship_info_kwargs)

def __readObjectInfo(obj_content: 'MutableMapping[str, Any]',
                     prefixes: 'Sequence[str]') -> 'ObjectInfo':

    model_metadata = obj_content.get('__model_attr_meta__')
    if model_metadata is not None:
        prefixes = model_metadata.get('parentpath', prefixes)

    model = obj_content.get('model')
    if model is not None:
        model, _ = resolvePrefix(model, prefixes)

        if model is None:
            raise ValueError(f'Object model not found')

    position = (obj_content.get('x', 0), obj_content.get('y', 0))
    angle = pi*obj_content.get('angle', 0)/180


    variables_content = obj_content.get('Variable')

    variables: 'Optional[MutableMapping[str, Any]]'
    if variables_content:
        variables = {variable['id']: variable['value']
                     for variable in variables_content}
    else:
        variables = None

    return ObjectInfo(model=model, position=position, angle=angle,
                      variables=variables)

def loadPhysicsEngine(engine_info: 'MutableMapping[str, Any]') \
        -> 'PhysicsEngineInfo':

    gravity_dict = engine_info.get('Gravity')
    if gravity_dict is not None:
        gravity = (gravity_dict.get('x', 0), gravity_dict.get('y', 0))
    else:
        gravity = (0, 0)

    return PhysicsEngineInfo(engine_info.get('damping', 1),
                             gravity,
                             engine_info.get('collision_slop', 0.1),
                             engine_info.get('collision_persistence', 3),
                             engine_info.get('iterations', 10))

def loadCommunicationEngine(engine_info: 'MutableMapping[str, Any]') \
        -> 'CommunicationEngine':

    return CommunicationEngine(engine_info.get('max_noise', 10),
                               engine_info.get('speed', 10000),
                               engine_info.get('negligible_intensity', 10000))

def loadScenario(scenario_info: 'MutableMapping[str, Any]',
                 prefixes: 'Sequence[str]' = (),
                 objective_loader=None) -> 'ScenarioInfo':

    scenario_content = scenario_info.get('Scenario', {})

    s_name = scenario_content.get('name', '<<nameless>>')
    ships = tuple(__readShipInfo(ship, prefixes)
                  for ship in scenario_info.get('Ship', ()))

    if objective_loader is None:
        load_objectives_func = loadObjectives
    else:
        load_objectives_func = objective_loader.load

    objectives = tuple(load_objectives_func(scenario_info.get('Objective', ())))

    objects = tuple(__readObjectInfo(obj, prefixes)
                    for obj in scenario_info.get('Object', ()))

    images = loadImages(scenario_info.get('Image', ()), prefixes)

    hidden_user_interface = scenario_content.get('hide_user_interface', False)

    comm_engine = loadCommunicationEngine(
        scenario_info.get('CommunicationEngine', {}))

    return ScenarioInfo(name=s_name, ships=ships, objectives=objectives,
                        visible_user_interface=not(hidden_user_interface),
                        visible_debug_window=scenario_content.get(
                            'debug', False),
                        communication_engine=comm_engine, objects=objects,
                        static_images=images,
                        physics_engine=loadPhysicsEngine(
                            scenario_info.get('PhysicsEngine', {})))
