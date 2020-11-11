
import functools
from typing import TYPE_CHECKING

from ...utils.errorgenerator import (
    ErrorGenerator, NormalDistributionErrorGenerator,
    TriangularDistributionErrorGenerator,
    UniformDistributionErrorGenerator
)

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

    @staticmethod
    def __loadNumber(info: 'MutableMapping[str, Any]', field: str,
                     default: float = 0) -> float:

        value = info.get(field, default)

        if not isinstance(value, (int, float)):
            raise TypeError(
                f'{field} must be a number and not {type(value)}')

        return value

    @staticmethod
    def __loadNumberInterval(info: 'MutableMapping[str, Any]', field: str,
                             min_, max_, default: float = 0) -> float:

        value = ErrorLoader.__loadNumber(info, field, default=default)

        if value < min_ or value > max_:
            raise ValueError(f'{field} must be a value between {min_} and '
                             f'{max_}, {value} is not a valid value')

        return value

    def __loadLinearError(self,
                          info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        error_max = self.__loadNumber(info, 'error_max')
        offset_max = self.__loadNumber(info, 'offset_max')
        error_max_minfac = self.__loadNumberInterval(
            info, 'error_max_minfac', 0, 1)

        return UniformDistributionErrorGenerator(
            error_max=error_max, offset_max=offset_max,
            error_max_minfac=error_max_minfac)

    def __loadTriangularError(
            self, info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        error_max = self.__loadNumber(info, 'error_max')
        left_error_max = self.__loadNumber(info, 'left_error_max',
                                           default=error_max)
        right_error_max = self.__loadNumber(info, 'right_error_max',
                                            default=error_max)
        offset_max = self.__loadNumber(info, 'offset_max')
        error_max_minfac = self.__loadNumberInterval(
            info, 'error_max_minfac', 0, 1, default=1)

        return TriangularDistributionErrorGenerator(
            left_error_max=left_error_max, right_error_max=right_error_max,
            offset_max=offset_max, error_max_minfac=error_max_minfac)

    def __loadNormalError(
            self, info: 'MutableMapping[str, Any]') -> ErrorGenerator:

        sigma = self.__loadNumber(info, 'sigma')
        offset_sigma = self.__loadNumber(info, 'offset_sigma')
        error_max_minfac = self.__loadNumberInterval(
            info, 'sigma_max_minfac', 0, 1)

        return NormalDistributionErrorGenerator(
            error_sigma=sigma, offset_sigma=offset_sigma,
            sigma_minfac=error_max_minfac)

    __CREATE_FUNCTIONS = {

        None: __loadLinearError,
        'uniform': __loadLinearError,
        'triangular': __loadTriangularError,
        'normal': __loadNormalError
    }
