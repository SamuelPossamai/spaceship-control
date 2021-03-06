
import functools
from typing import TYPE_CHECKING

from .customloader import CustomLoader

from .. import configfilevariables

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

    def _addCustom(self, config: 'MutableMapping[str, Any]', model_type: 'Any',
                   model_info: 'MutableMapping[str, Any]') -> None:

        mode = config.get('mode')
        if mode == 'static':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicObjectiveFunction, model_info)
        elif mode is None or mode == 'dynamic':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicObjectiveFunction, model_info)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    @staticmethod
    def __createCustomStaticObjectiveFunction(
            objective_content: 'MutableMapping[str, Any]',
            loader: 'ObjectiveLoader',
            _custom_objective_info: 'MutableMapping[str, Any]') -> 'Objective':

        return loader.__createObjectiveGroup(objective_content) # pylint: disable=protected-access

    @staticmethod
    def __createCustomDynamicObjectiveFunction(
            objective_content: 'MutableMapping[str, Any]',
            loader: 'ObjectiveLoader',
            _custom_objective_info: 'MutableMapping[str, Any]') -> 'Objective':

        variables = {variable['id']: variable['value'] for variable in
                     custom_objective_info.get('Variable', ())}

        configfilevariables.subVariables(objective_content,
                                         variables=variables,
                                         enabled=True)

        return loader.__createObjectiveGroup(objective_content) # pylint: disable=protected-access

    def load(self, objectives: 'Sequence[MutableMapping[str, Any]]') \
            -> 'Sequence[Objective]':

        create_functions = self._load_functions

        return tuple(create_functions[objective['type']](self, objective)
                     for objective in objectives)

    def __createGoToObjective(self, # pylint: disable=no-self-use
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
