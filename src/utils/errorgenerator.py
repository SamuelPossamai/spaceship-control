
from abc import ABC, abstractmethod
import random

import numpy

class ErrorGenerator(ABC):

    def __init__(self, offset: float) -> None:
        self.__offset = offset

    @property
    def offset(self):
        return self.__offset

    @abstractmethod
    def _applyValError(self, val: float) -> float:
        pass

    def __call__(self, val: float) -> float:
        return val + self._applyValError(val) + self.__offset

    @staticmethod
    def _calculateDecreaseFactor(factor, random_func):

        if factor == 1:
            return 1

        return factor + random_func()*(1 - factor)

    def toDict(self):
        return {}

class UniformDistributionErrorGenerator(ErrorGenerator):

    def __init__(self,
                 error_max: float,
                 offset_max: float,
                 error_max_minfac: float = 1,
                 offset=None) -> None:
        super().__init__(self._getRandom(offset_max))

        self.__offset_max = offset_max

        self.__error_max_before = error_max

        error_max *= self._calculateDecreaseFactor(
            error_max_minfac, random.random)

        self.__error_max = error_max

    @property
    def max_offset(self) -> float:
        return self.__offset_max

    @property
    def max_error(self) -> float:
        return self.__error_max_before

    def _getRandom(self, value: float) -> float:
        return (2*random.random() - 1)*value

    def _applyValError(self, val: float) -> float:

        if self.__error_max == 0:
            return 0

        return self._getRandom(self.__error_max)

    def toDict(self):
        return {
            'max-offset': self.__offset_max,
            'max-error': self.__error_max_before,
            'type': 'uniform'
        }

class NormalDistributionErrorGenerator(ErrorGenerator):

    def __init__(self,
                 error_sigma: float,
                 offset_sigma: float,
                 sigma_minfac: float = 1) -> None:
        super().__init__(self._getRandom(offset_sigma))

        self.__base_error_sigma = error_sigma

        error_sigma *= self._calculateDecreaseFactor(
            sigma_minfac, random.random)

        self.__error_sigma = error_sigma
        self.__offset_sigma = offset_sigma

    def _getRandom(self, sigma: float) -> float:
        return numpy.random.normal(0, sigma)

    def _applyValError(self, val: float) -> float:

        if self.__error_sigma == 0:
            return 0

        return self._getRandom(self.__error_sigma)

    def toDict(self):
        return {
            'error-sigma': self.__base_error_sigma,
            'offset-sigma': self.__offset_sigma,
            'type': 'normal'
        }

class TriangularDistributionErrorGenerator(ErrorGenerator):

    def __init__(self,
                 left_error_max: float,
                 right_error_max: float,
                 offset_max: float,
                 error_max_minfac: float = 1) -> None:
        super().__init__(self._getRandom(offset_max, offset_max))

        self.__offset_max = offset_max

        self.__left_error_max_before = left_error_max
        self.__right_error_max_before = right_error_max

        left_error_max *= self._calculateDecreaseFactor(
            error_max_minfac, random.random)

        right_error_max *= self._calculateDecreaseFactor(
            error_max_minfac, random.random)

        self.__left_error_max = left_error_max
        self.__right_error_max = right_error_max

    def _getRandom(self, left: float, right: float) -> float:
        return numpy.random.triangular(0, -left, 0, +right)

    def _applyValError(self, val: float) -> float:

        if self.__left_error_max == 0 and self.__right_error_max == 0:
            return 0

        return self._getRandom(self.__left_error_max, self.__right_error_max)

    def toDict(self):
        return {
            'max-offset': self.__offset_max,
            'left-max-offset': self.__left_error_max_before,
            'right-max-offset': self.__right_error_max_before,
            'max-error': max(self.__left_error_max_before,
                             self.__right_error_max_before),
            'type': 'triangular'
        }
