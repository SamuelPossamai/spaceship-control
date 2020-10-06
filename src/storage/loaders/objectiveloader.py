
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

    def clearCustoms(self) -> None:
        self.__create_functions = self.__OBJECTIVE_CREATE_FUNCTIONS.copy()

    def addCustom(self, custom_objective_info):

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
                lambda loader, objective_content, \
                    obj_model_info=obj_model_info: \
                        loader.__createCustomDynamicObjectiveFunction(
                            objective_content, obj_model_info)
        elif mode is None or mode == 'dynamic':
            self.__create_functions[type_] = \
                lambda loader, objective_content, \
                    obj_model_info=obj_model_info: \
                        loader.__createCustomDynamicObjectiveFunction(
                            objective_content, obj_model_info)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    def __createCustomStaticObjectiveFunction(
            self, custom_objective_info: 'MutableMapping[str, Any]',
            objective_content: 'MutableMapping[str, Any]') -> 'Objective':

        return self.__createObjectiveGroup(objective_content)

    def __createCustomDynamicObjectiveFunction(
            self, custom_objective_info: 'MutableMapping[str, Any]',
            objective_content: 'MutableMapping[str, Any]') -> 'Objective':

        configfilevariables.subVariables(objective_content)

        return self.__createObjectiveGroup(objective_content)

    def load(self, objectives: 'Sequence[MutableMapping[str, Any]]') \
            -> 'Sequence[Objective]':

        create_functions = self.__create_functions

        return tuple(create_functions[objective['type']](self, objective)
                     for objective in objectives)

    def __createGoToObjective(self,
                              objective_content: 'MutableMapping[str, Any]') \
            -> 'GoToObjective':

        position = (objective_content['x'], objective_content['y'])
        distance = objective_content['distance']

        kwargs = {key: value for key, value in objective_content.items()
                if key in ('name', 'description', 'negation', 'valid_ships')}

        return GoToObjective(position, distance, **kwargs)

    def __createObjectiveGroup(self,
                               objective_content: 'MutableMapping[str, Any]') \
            -> 'ObjectiveGroup':

        valid_kwargs = ('name', 'description', 'required_quantity',
                        'sequential', 'negation', 'valid_ships')

        kwargs = {key: value for key, value in objective_content.items()
                  if key in valid_kwargs}

        return ObjectiveGroup(self.load(objective_content['Objective']),
                              **kwargs)

    def __createTimedObjectiveGroup(
            self, objective_content: 'MutableMapping[str, Any]') \
                -> 'TimedObjectiveGroup':

        valid_kwargs = ('name', 'description', 'required_quantity',
                        'sequential', 'time_limit', 'negation', 'valid_ships')

        kwargs = {key: value for key, value in objective_content.items()
                if key in valid_kwargs}

        return TimedObjectiveGroup(
            self.load(objective_content['Objective']), **kwargs)

    __OBJECTIVE_CREATE_FUNCTIONS = {

        'goto': __createGoToObjective,
        'list': __createObjectiveGroup,
        'timed-list': __createTimedObjectiveGroup
    }
