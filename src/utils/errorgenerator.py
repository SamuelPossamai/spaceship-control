
from abc import ABC, abstractmethod
import random

import numpy

class ErrorGenerator(ABC):

    def __init__(self, offset: float) -> None:
        self.__offset = offset

    @abstractmethod
    def _applyValError(self, val: float) -> float:
        pass

    def __call__(self, val: float) -> float:
        return self._applyValError(val) + self.__offset

class UniformDistributionErrorGenerator(ErrorGenerator):

    def __init__(self,
                 error_max: float,
                 offset_max: float,
                 error_max_minfac: float = 1,
                 offset=None) -> None:
        super().__init__(self._getRandom(offset_max))

        self.__offset_max = offset_max

        self.__error_max_before = error_max

        if error_max_minfac != 1:
            error_max *= error_max_minfac + \
                random.random()*(1 - error_max_minfac)

        self.__error_max = error_max

    @property
    def max_offset(self) -> float:
        return self.__offset_max

    @property
    def _real_max_error(self) -> float:
        return self.__error_max

    @property
    def max_error(self) -> float:
        return self.__error_max_before

    def _getRandom(self, value: float) -> float:
        return (2*random.random() - 1)*value

    def _applyValError(self, val: float) -> float:

        if self.__error_max == 0:
            return 0

        return self._getRandom(self.__error_max)

class NormalDistributionErrorGenerator(UniformDistributionErrorGenerator):

    def _getRandom(self, value: float) -> float:
        return numpy.random.normal(value/2)

    def _applyValError(self, val: float) -> float:

        if self.__error_max == 0:
            return 0

        return self._getRandom(self.__error_max)

class TriangularDistributionErrorGenerator(UniformDistributionErrorGenerator):

    def _getRandom(self, value: float) -> float:
        return numpy.random.triangular(0, val - self.__error_max, val,
                                       val + self.__error_max)

    def _applyValError(self, val: float) -> float:

        if self.__error_max == 0:
            return 0

        return self._getRandom(self.__error_max)
