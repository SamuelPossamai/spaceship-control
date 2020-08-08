
import bisect

class Interval:

    def __init__(self, start: 'Union[int, float]',
                 end: 'Union[int, float]' = None) -> None:
        self.__start = start
        if end is None:
            self.__end = start
        else:
            self.__end = end

    @property
    def start(self) -> 'Union[int, float]':
        return self.__start

    @property
    def end(self) -> 'Union[int, float]':
        return self.__end

    def isInside(self, val: 'Union[int, float]') -> bool:
        return self.__start <= val <= self.__end

    def isConstant(self) -> bool:
        return self.__start == self.__end

class IntervalSet:

    def __init__(self, intervals: 'Iterable[Interval]') -> None:

        self.__sequence = sorted(interval for interval in intervals
                                 if not interval.isConstant())
        self.__constants = set(interval for interval in intervals
                               if interval.isConstant())

    def add(self, interval: Interval) -> None:

        if interval.isConstant():
            self.__constants.add(interval)
        else:
            bisect.insort(self.__sequence, interval)

    def isInside(self, val) -> bool:

        if val in self.__constants:
            return True

        for interval in self.__sequence:

            if interval.start > val:
                break

            if val <= interval.end:
                return True

        return False

    def __len__(self) -> int:
        return len(self.__sequence)

    def __iter__(self):
        return iter(self.__sequence)
