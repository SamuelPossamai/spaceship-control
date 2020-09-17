
from typing import TYPE_CHECKING

from .. import fileinfo

from ...objectives.objective import ObjectiveGroup
from ...objectives.gotoobjective import GoToObjective
from ...objectives.timedobjective import TimedObjectiveGroup

if TYPE_CHECKING:
    from typing import Any, MutableMapping, Sequence
    from ...objectives.objective import Objective

def __createGoToObjective(objective_content: 'MutableMapping[str, Any]') \
        -> 'GoToObjective':

    position = (objective_content['x'], objective_content['y'])
    distance = objective_content['distance']

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description', 'negation', 'valid_ships')}

    return GoToObjective(position, distance, **kwargs)

def __createObjectiveGroup(objective_content: 'MutableMapping[str, Any]') \
        -> 'ObjectiveGroup':

    valid_kwargs = ('name', 'description', 'required_quantity', 'sequential',
                    'negation', 'valid_ships')

    kwargs = {key: value for key, value in objective_content.items()
              if key in valid_kwargs}

    return ObjectiveGroup(loadObjectives(objective_content['Objective']),
                          **kwargs)

def __createTimedObjectiveGroup(objective_content: 'MutableMapping[str, Any]') \
        -> 'TimedObjectiveGroup':

    valid_kwargs = ('name', 'description', 'required_quantity', 'sequential',
                    'time_limit', 'negation', 'valid_ships')

    kwargs = {key: value for key, value in objective_content.items()
              if key in valid_kwargs}

    return TimedObjectiveGroup(loadObjectives(objective_content['Objective']),
                               **kwargs)

__OBJECTIVE_CREATE_FUNCTIONS = {

    'goto': __createGoToObjective,
    'list': __createObjectiveGroup,
    'timed-list': __createTimedObjectiveGroup
}

def loadCustomObjectives(custom_objectives):

    for objective in custom_objectives:
        loadCustomObjectives(objective.children())

def loadObjectives(objectives: 'Sequence[MutableMapping[str, Any]]') \
        -> 'Sequence[Objective]':

    custom_objectives = fileinfo.FileInfo().listFilesTree(
        fileinfo.FileInfo.FileDataType.OBJECTIVE)

    return tuple(__OBJECTIVE_CREATE_FUNCTIONS[objective['type']](objective)
                 for objective in objectives)
