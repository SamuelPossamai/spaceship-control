
from typing import TYPE_CHECKING

from .. import fileinfo, configfilevariables

from ...objectives.objective import ObjectiveGroup
from ...objectives.gotoobjective import GoToObjective
from ...objectives.timedobjective import TimedObjectiveGroup

if TYPE_CHECKING:
    from typing import Any, MutableMapping, Sequence
    from ...objectives.objective import Objective

def loadObjectives(objectives: 'Sequence[MutableMapping[str, Any]]') \
        -> 'Sequence[Objective]':

    return ObjectiveLoader().load(objectives)

class ObjectiveLoader:

    def __init__(self) -> None:
        self.__create_functions = self.__OBJECTIVE_CREATE_FUNCTIONS.copy()

    def clearCustomObjectives(self) -> None:
        self.__create_functions = self.__OBJECTIVE_CREATE_FUNCTIONS.copy()

    def addCustomObjective(self, custom_objective_info):

        config = custom_objective_info.get('Configuration')

        if config is None:
            raise Exception('Objective \'Configuration\' is required')

        obj_model_info = custom_objective_info.get('ModelInfo')

        if obj_model_info is None:
            raise Exception('Objective \'ModelInfo\' is required')

        type_ = config.get('type')
        if type_ is None:
            raise Exception('Objective type is required')

        if type_ in self.__create_functions:
            raise Exception(f'Objective type \'{type_}\' already in use')

        mode = config.get('mode')
        if mode == 'static':
            self.__create_functions[type_] = \
                lambda objective_content, \
                    obj_model_info=obj_model_info: \
                        self.__createCustomDynamicObjectiveFunction(
                            obj_model_info, objective_content)
        elif mode == 'dynamic':
            self.__create_functions[type_] = \
                lambda objective_content, \
                    obj_model_info=obj_model_info: \
                        self.__createCustomDynamicObjectiveFunction(
                            obj_model_info, objective_content)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    @staticmethod
    def __createCustomStaticObjectiveFunction(
            custom_objective_info: 'MutableMapping[str, Any]',
            objective_content: 'MutableMapping[str, Any]') -> 'Objective':

        return create_functions[objective['type']](objective)

    @staticmethod
    def __createCustomDynamicObjectiveFunction(
            custom_objective_info: 'MutableMapping[str, Any]',
            objective_content: 'MutableMapping[str, Any]') -> 'Objective':

        configfilevariables.subVariables(objective_content)

        return create_functions[objective['type']](objective)

    def load(self, objectives: 'Sequence[MutableMapping[str, Any]]') \
            -> 'Sequence[Objective]':

        create_functions = self.__create_functions

        return tuple(create_functions[objective['type']](objective)
                     for objective in objectives)

    @staticmethod
    def __createGoToObjective(_loader: 'ObjectiveLoader',
                              objective_content: 'MutableMapping[str, Any]') \
            -> 'GoToObjective':

        position = (objective_content['x'], objective_content['y'])
        distance = objective_content['distance']

        kwargs = {key: value for key, value in objective_content.items()
                if key in ('name', 'description', 'negation', 'valid_ships')}

        return GoToObjective(position, distance, **kwargs)

    @staticmethod
    def __createObjectiveGroup(loader: 'ObjectiveLoader',
                               objective_content: 'MutableMapping[str, Any]') \
            -> 'ObjectiveGroup':

        valid_kwargs = ('name', 'description', 'required_quantity',
                        'sequential', 'negation', 'valid_ships')

        kwargs = {key: value for key, value in objective_content.items()
                if key in valid_kwargs}

        return ObjectiveGroup(loader.load(objective_content['Objective']),
                              **kwargs)

    @staticmethod
    def __createTimedObjectiveGroup(
            loader: 'ObjectiveLoader',
            objective_content: 'MutableMapping[str, Any]') \
                -> 'TimedObjectiveGroup':

        valid_kwargs = ('name', 'description', 'required_quantity',
                        'sequential', 'time_limit', 'negation', 'valid_ships')

        kwargs = {key: value for key, value in objective_content.items()
                if key in valid_kwargs}

        return TimedObjectiveGroup(
            loader.load(objective_content['Objective']), **kwargs)

    __OBJECTIVE_CREATE_FUNCTIONS = {

        'goto': __createGoToObjective,
        'list': __createObjectiveGroup,
        'timed-list': __createTimedObjectiveGroup
    }
