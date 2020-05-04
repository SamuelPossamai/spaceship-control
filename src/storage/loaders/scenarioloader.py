
from math import pi
from collections import namedtuple

from ..configfileinheritance import resolvePrefix

from ...objectives.objective import ObjectiveGroup
from ...objectives.gotoobjective import GoToObjective
from ...objectives.timedobjective import TimedObjectiveGroup

from ...devices.communicationdevices import CommunicationEngine

StaticImageInfo = namedtuple('StaticImageInfo',
                             ('name', 'width', 'height', 'x', 'y'))

ObjectInfo = namedtuple('ObjectInfo', ('model', 'position', 'angle'))

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

def __createGoToObjective(objective_content) -> 'GoToObjective':

    position = (objective_content['x'], objective_content['y'])
    distance = objective_content['distance']

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description')}

    return GoToObjective(position, distance, **kwargs)

def __createObjectiveGroup(objective_content) -> 'ObjectiveGroup':

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description', 'required_quantity')}

    return ObjectiveGroup(loadObjectives(objective_content['Objective']),
                          **kwargs)

def __createTimedObjectiveGroup(objective_content) -> 'TimedObjectiveGroup':

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description', 'time_limit')}

    return TimedObjectiveGroup(loadObjectives(objective_content['Objective']),
                               **kwargs)

__OBJECTIVE_CREATE_FUNCTIONS = {

    'goto': __createGoToObjective,
    'list': __createObjectiveGroup,
    'timed-list': __createTimedObjectiveGroup
}

def __resolveShipModelPrefix(model, prefixes):

    model_after, _ = resolvePrefix(model, prefixes)

    if model_after is None:
        raise ValueError(f'Ship model not found \'{model}\'')

    return model_after

def __readShipInfo(ship_content, prefixes) -> 'ShipInfo':

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

def __readObjectInfo(obj_content, prefixes) -> 'ObjectInfo':

    model = obj_content.get('model')
    if model is not None:
        model, _ = resolvePrefix(model, prefixes)

        if model is None:
            raise ValueError(f'Object model not found')

    position = (obj_content.get('x', 0), obj_content.get('y', 0))
    angle = pi*obj_content.get('angle', 0)/180

    return ObjectInfo(model=model, position=position, angle=angle)

def __readImageInfo(image_content, prefixes) -> 'StaticImageInfo':

    image_path = image_content['path']

    image_path, _ = resolvePrefix(image_path, prefixes)
    return StaticImageInfo(image_path,
                           width=image_content.get('width'),
                           height=image_content.get('height'),
                           x=image_content.get('x', 0),
                           y=image_content.get('y', 0))

def loadPhysicsEngine(engine_info: 'Dict[str, Any]'):

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

def loadCommunicationEngine(engine_info: 'Dict[str, Any]'):

    return CommunicationEngine(engine_info.get('max_noise', 10),
                               engine_info.get('speed', 10000),
                               engine_info.get('negligible_intensity', 10000))

def loadObjectives(objectives):
    return tuple(__OBJECTIVE_CREATE_FUNCTIONS[objective['type']](objective)
                 for objective in objectives)

def loadScenario(scenario_info: 'Dict[str, Any]',
                 prefixes=()) -> 'ScenarioInfo':

    scenario_content = scenario_info.get('Scenario', {})

    s_name = scenario_content.get('name', '<<nameless>>')
    ships = tuple(__readShipInfo(ship, prefixes)
                  for ship in scenario_info.get('Ship', ()))

    objectives = tuple(loadObjectives(scenario_info.get('Objective', ())))

    objects = tuple(__readObjectInfo(obj, prefixes)
                    for obj in scenario_info.get('Object', ()))

    images = tuple(__readImageInfo(image, prefixes)
                   for image in scenario_info.get('Image', ()))

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
