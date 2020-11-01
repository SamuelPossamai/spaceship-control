
import functools
from typing import TYPE_CHECKING

from ...utils.errorgenerator import ErrorGenerator

from .customloader import CustomLoader

if TYPE_CHECKING:
    from typing import Any, MutableMapping, Sequence

def loadError(info: 'Sequence[MutableMapping[str, Any]]') \
        -> 'Sequence[Objective]':

    return ErrorLoader().load(info)

class ErrorLoader(CustomLoader):

    def __init__(self) -> None:
        super().__init__(self.__CREATE_FUNCTIONS, label='Error')

    def _addCustom(self, config, model_type, model_info):

        mode = config.get('mode')
        if mode == 'static':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicFunction, model_info)
        elif mode is None or mode == 'dynamic':
            self._load_functions[model_type] = functools.partial(
                self.__createCustomDynamicFunction, model_info)
        else:
            raise Exception(f'Invalid mode \'{mode}\'')

    @staticmethod
    def __createCustomStaticFunction(
            content: 'MutableMapping[str, Any]', loader,
            custom_info: 'MutableMapping[str, Any]'):

        raise NotImplementedError()

    @staticmethod
    def __createCustomDynamicFunction(
            content: 'MutableMapping[str, Any]', loader,
            custom_info: 'MutableMapping[str, Any]'):

        raise NotImplementedError()

    def load(self, info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        create_functions = self._load_functions

        return create_functions[info.get('type')](self, info)

    def __loadLinearError(self,
                          info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        error_max = info.get('error_max', 0)

        if not isinstance(error_max, (int, float)):
            raise TypeError(
                f'error_max must be a number and not {type(error_max)}')

        offset_max = info.get('offset_max', 0)

        if not isinstance(offset_max, (int, float)):
            raise TypeError(
                f'offset_max must be a number and not {type(offset_max)}')

        error_max_minfac = info.get('error_max_minfac', 1)

        if not isinstance(error_max_minfac, (int, float)):
            raise TypeError('error_max_minfac must be a '
                            f'number and not {type(error_max_minfac)}')

        if error_max_minfac < 0 or error_max_minfac > 1:
            raise ValueError('error_max_minfac must be a value between 0 and 1'
                             f', {error_max_minfac} is not a valid value')

        return ErrorGenerator(error_max=error_max,
                              offset_max=offset_max,
                              error_max_minfac=error_max_minfac)

    __CREATE_FUNCTIONS = {

        None: __loadLinearError,
        'goto': __loadLinearError
    }
