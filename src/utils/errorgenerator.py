
import random
import numpy

class ErrorGenerator:

    def __init__(self,
                 error_max: float,
                 offset_max: float,
                 error_max_minfac: float = 1):

        self.__error_max_before = error_max

        if error_max_minfac != 1:
            error_max *= error_max_minfac + \
                random.random()*(1 - error_max_minfac)

        self.__error_max = error_max
        self.__offset_max = offset_max
        self.__offset = (2*random.random() - 1)*offset_max

    @property
    def _real_max_error(self) -> float:
        return self.__error_max

    @property
    def max_error(self) -> float:
        return self.__error_max_before

    @property
    def max_offset(self) -> float:
        return self.__offset_max

    def __call__(self, val: float) -> float:
        val += self.__offset
        if self.__error_max == 0:
            return val

        return val + (2*random.random() - 1)*self.__error_max

class NormalDistributionErrorGenerator(ErrorGenerator):

    def __call__(self, val: float) -> float:
        val += self.__offset
        if self.__error_max == 0:
            return val

        return val + numpy.random.normal(val, self.__error_max/2, 1000)
