
from typing import TYPE_CHECKING

from .customloader import CustomLoader

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

class ObjectiveLoader(CustomLoader):

    def __init__(self) -> None:
        super().__init__(self.__OBJECTIVE_CREATE_FUNCTIONS, label='Objective')

    def _addCustom(self, config, model_type, model_info):

        mode = config.get('mode')
        if mode == 'static':
            self._load_functions[model_type] = \
                lambda loader, objective_content, \
                    obj_model_info=model_info: \
                        loader.__createCustomDynamicObjectiveFunction(
                            objective_content, model_info)
        elif mode is None or mode == 'dynamic':
            self._load_functions[model_type] = \
                lambda loader, objective_content, \
                    obj_model_info=model_info: \
                        loader.__createCustomDynamicObjectiveFunction(
                            objective_content, model_info)
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

        create_functions = self._load_functions

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
