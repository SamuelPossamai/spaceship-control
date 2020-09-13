
from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING

import random
import math

from pymunk import Vec2d

from .device import DefaultDevice

if TYPE_CHECKING:
    from typing import Any, List, Tuple, Dict, Callable
    from ..utils.errorgenerator import ErrorGenerator
    from .structure import StructuralPart

class CommunicationEngine:

    class Receiver(ABC):

        @abstractmethod
        def signalReceived(self, intensity: float, frequency: float) -> None:
            pass

        @abstractproperty
        def position(self) -> 'Tuple[float, float]':
            pass

    class _Signal:

        def __init__(self, start_point: 'Vec2d', initial_intensity: float,
                     frequency: float, engine: 'CommunicationEngine') -> None:

            self.__start = start_point
            self.__inital_intensity = initial_intensity
            self.__engine = engine
            self.__cur_distance: float = 0
            self.__sqrd_min_distance: float = 0
            self.__sqrd_max_distance: float = 0
            self.__cur_intensity = initial_intensity
            self.__frequency = frequency
            self.__valid = True

            self.__calcDist()

        def __calcDist(self) -> None:

            half_speed = self.__engine._speed/2 # pylint: disable=protected-access

            self.__sqrd_min_distance = (
                max(0, self.__cur_distance - half_speed))**2
            self.__sqrd_max_distance = (self.__cur_distance + half_speed)**2

        def step(self) -> None:
            self.__cur_distance += self.__engine._speed # pylint: disable=protected-access
            self.__calcDist()

        def sendTo(self, receiver: 'CommunicationEngine.Receiver') -> None:
            dist = Vec2d(receiver.position).get_dist_sqrd(self.__start)

            if self.__sqrd_min_distance < dist < self.__sqrd_max_distance:
                noise = (random.random() - 0.5)*self.__engine._noise_max # pylint: disable=protected-access
                intensity = self.__inital_intensity if dist < 1 else \
                    self.__inital_intensity/dist
                if intensity < self.__engine._ignore_lesser: # pylint: disable=protected-access
                    self.__valid = False

                if intensity > 2*abs(noise):
                    receiver.signalReceived(abs(intensity + noise),
                                            self.__frequency)

        def isValid(self) -> bool:
            return self.__valid

    def __init__(self, max_noise: float, speed: float,
                 negligible_intensity: float) -> None:
        self._noise_max = max_noise
        self._ignore_lesser = negligible_intensity
        self._speed = speed

        self.__signals: 'List[CommunicationEngine._Signal]' = []
        self.__receivers: 'List[CommunicationEngine.Receiver]' = []

    def step(self) -> None:

        invalid_signals_indexes = []
        signals = self.__signals
        for i, signal in enumerate(signals):
            if not signal.isValid():
                invalid_signals_indexes.append(i)
                continue
            for receiver in self.__receivers:
                signal.sendTo(receiver)
            signal.step()

        if invalid_signals_indexes:
            for i in reversed(invalid_signals_indexes):
                signals[i] = signals[len(invalid_signals_indexes) - i - 1]

            del signals[-len(invalid_signals_indexes):]

    def newSignal(self, start_point: 'Vec2d', initial_intensity: float,
                  frequency: float) -> None:
        self.__signals.append(CommunicationEngine._Signal(
            start_point, initial_intensity, frequency, self))

    def addReceiver(self, receiver: 'CommunicationEngine.Receiver') -> None:
        self.__receivers.append(receiver)

    def clear(self) -> None:
        self.__receivers.clear()
        self.__signals.clear()

class BasicReceiver(DefaultDevice, CommunicationEngine.Receiver):

    def __init__(self, part: 'StructuralPart', sensibility: float,
                 frequency: float, frequency_tolerance: float = 0.1,
                 engine: 'CommunicationEngine' = None,
                 device_type: str = 'basic-receiver') -> None:
        DefaultDevice.__init__(self, device_type=device_type)
        CommunicationEngine.Receiver.__init__(self)

        self.__part = part
        self._sensibility = sensibility
        self._frequency = frequency
        self._frequency_tol = frequency_tolerance

        self.__received_signals: 'List[float]' = []

        if engine is not None:
            engine.addReceiver(self)

    def act(self) -> None:
        pass

    @property
    def position(self) -> 'Tuple[float, float]':
        return self.__part.position

    def signalReceived(self, intensity: float, frequency: float) -> None:

        frequency_diff = abs(frequency - self._frequency)

        if abs(frequency_diff) > self._frequency_tol:
            return

        if frequency_diff != 0:
            intensity *= \
                (self._frequency_tol - frequency_diff)/self._frequency_tol

        if intensity <= self._sensibility:
            return

        self.__received_signals.append(intensity - self._sensibility)

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return DefaultDevice.command(self, command,
                                     BasicReceiver.__COMMANDS, *args)

    def __getReceived(self) -> str:
        signals = ','.join(str(signal) for signal in self.__received_signals)
        self.__received_signals.clear()
        return signals

    __COMMANDS = {
        'get-frequency': lambda self: self._frequency, # pylint: disable=protected-access
        'get-received': __getReceived
    }

class ConfigurableReceiver(BasicReceiver):

    def __init__(self, *args: 'Any', min_frequency: float = 0,
                 max_frequency: float = math.inf, **kwargs: 'Any') -> None:
        super().__init__(*args, **kwargs, device_type='receiver')

        self.__min_freq = min_frequency
        self.__max_freq = max_frequency

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, ConfigurableReceiver.__COMMANDS, *args)

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: 'float') -> None:
        if self.__min_freq <= self._frequency <= self.__max_freq:
            self._frequency = value

    __COMMANDS: 'Dict[str, Callable]' = {
        'set-frequency': lambda self, val:
                         ConfigurableReceiver.frequency.fset(self, float(val)),
        'min-frequency': lambda self: self.__min_freq, # pylint: disable=protected-access
        'max-frequency': lambda self: self.__max_freq # pylint: disable=protected-access
    }

class BasicSender(DefaultDevice):

    def __init__(self, part: 'StructuralPart', engine: 'CommunicationEngine',
                 intensity: float, frequency: float,
                 frequency_err_gen: 'ErrorGenerator' = None,
                 intensity_err_gen: 'ErrorGenerator' = None,
                 device_type: str = 'basic-sender') -> None:
        super().__init__(device_type=device_type)

        self.__part = part
        self.__engine = engine
        self.__int_err_gen = intensity_err_gen
        self.__freq_err_gen = frequency_err_gen
        self._frequency = frequency
        self._intensity = intensity

    def act(self) -> None:
        pass

    def send(self) -> None:

        if self.__freq_err_gen is None:
            frequency = self._frequency
        else:
            frequency = abs(self.__freq_err_gen(self._frequency))

        if self.__int_err_gen is None:
            intensity = self._intensity
        else:
            intensity = abs(self.__int_err_gen(self._intensity))

        self.__engine.newSignal(self.__part.position, intensity, frequency)

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, BasicSender.__COMMANDS, *args)

    __COMMANDS: 'Dict[str, Callable]' = {
        'get-frequency': lambda self: self._frequency, # pylint: disable=protected-access
        'get-intensity': lambda self: self._intensity, # pylint: disable=protected-access
        'send-signal': send
    }

class ConfigurableSender(BasicSender):

    def __init__(self, *args: 'Any', min_frequency: float = 0,
                 max_frequency: float = math.inf, min_intensity: float = 0,
                 max_intensity: float = math.inf, **kwargs: 'Any'):
        super().__init__(*args, **kwargs, device_type='sender')

        self.__min_freq = min_frequency
        self.__max_freq = max_frequency
        self.__min_int = min_intensity
        self.__max_int = max_intensity

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, ConfigurableSender.__COMMANDS, *args)

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        if self.__min_freq <= self._frequency <= self.__max_freq:
            self._frequency = value

    @property
    def intensity(self) -> float:
        return self._intensity

    @intensity.setter
    def intensity(self, value: float) -> None:
        if self.__min_int <= self._intensity <= self.__max_int:
            self._intensity = value

    __COMMANDS: 'Dict[str, Callable]' = {
        'set-frequency': lambda self, val:
                         ConfigurableSender.frequency.fset(self, float(val)),
        'set-intensity': lambda self, val:
                         ConfigurableSender.intensity.fset(self, float(val)),
        'min-frequency': lambda self: self.__min_freq, # pylint: disable=protected-access
        'max-frequency': lambda self: self.__max_freq, # pylint: disable=protected-access
        'min-intensity': lambda self: self.__min_int, # pylint: disable=protected-access
        'max-intensity': lambda self: self.__max_int # pylint: disable=protected-access
    }
