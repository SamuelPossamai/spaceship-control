
from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING

import random
import math

from pymunk import Vec2d

from .device import DefaultDevice

if TYPE_CHECKING:
    from typing import Any, List

class CommunicationEngine:

    class Receiver(ABC):

        @abstractmethod
        def signalReceived(self, intensity, frequency):
            pass

        @abstractproperty
        def position(self):
            pass

    class _Signal:

        def __init__(self, start_point, initial_intensity, frequency, engine):

            self.__start = start_point
            self.__inital_intensity = initial_intensity
            self.__engine = engine
            self.__cur_distance = 0
            self.__sqrd_min_distance = 0
            self.__sqrd_max_distance = 0
            self.__cur_intensity = initial_intensity
            self.__frequency = frequency
            self.__valid = True

            self.__calcDist()

        def __calcDist(self):

            half_speed = self.__engine._speed/2 # pylint: disable=protected-access

            self.__sqrd_min_distance = (
                max(0, self.__cur_distance - half_speed))**2
            self.__sqrd_max_distance = (self.__cur_distance + half_speed)**2

        def step(self):
            self.__cur_distance += self.__engine._speed # pylint: disable=protected-access
            self.__calcDist()

        def sendTo(self, receiver):
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

        def isValid(self):
            return self.__valid

    def __init__(self, max_noise, speed, negligible_intensity):
        self._noise_max = max_noise
        self._ignore_lesser = negligible_intensity
        self._speed = speed

        self.__signals = []
        self.__receivers = []

    def step(self):

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

    def newSignal(self, start_point, initial_intensity, frequency):
        self.__signals.append(CommunicationEngine._Signal(
            start_point, initial_intensity, frequency, self))

    def addReceiver(self, receiver):
        self.__receivers.append(receiver)

    def clear(self):
        self.__receivers.clear()
        self.__signals.clear()

class BasicReceiver(DefaultDevice, CommunicationEngine.Receiver):

    def __init__(self, part, sensibility, frequency, frequency_tolerance=0.1,
                 engine=None, device_type='basic-receiver'):
        DefaultDevice.__init__(self, device_type=device_type)
        CommunicationEngine.Receiver.__init__(self)

        self.__part = part
        self._sensibility = sensibility
        self._frequency = frequency
        self._frequency_tol = frequency_tolerance

        self.__received_signals = []

        if engine is not None:
            engine.addReceiver(self)

    def act(self):
        pass

    @property
    def position(self):
        return self.__part.position

    def signalReceived(self, intensity, frequency):

        frequency_diff = abs(frequency - self._frequency)

        if abs(frequency_diff) > self._frequency_tol:
            return

        if frequency_diff != 0:
            intensity *= \
                (self._frequency_tol - frequency_diff)/self._frequency_tol

        if intensity <= self._sensibility:
            return

        self.__received_signals.append(intensity - self._sensibility)

    def command(self, command: 'List[str]', *args) -> 'Any':
        return DefaultDevice.command(self, command,
                                     BasicReceiver.__COMMANDS, *args)

    def __getReceived(self):
        signals = ','.join(str(signal) for signal in self.__received_signals)
        self.__received_signals.clear()
        return signals

    __COMMANDS = {
        'get-frequency': lambda self: self._frequency, # pylint: disable=protected-access
        'get-received': __getReceived
    }

class ConfigurableReceiver(BasicReceiver):

    def __init__(self, *args, min_frequency=0, max_frequency=math.inf,
                 **kwargs):
        super().__init__(*args, **kwargs, device_type='receiver')

        self.__min_freq = min_frequency
        self.__max_freq = max_frequency

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, ConfigurableReceiver.__COMMANDS, *args)

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        if self.__min_freq <= self._frequency <= self.__max_freq:
            self._frequency = value

    __COMMANDS = {
        'set-frequency': lambda self, val:
                         ConfigurableReceiver.frequency.fset(self, float(val)),
        'min-frequency': lambda self: self.__min_freq, # pylint: disable=protected-access
        'max-frequency': lambda self: self.__max_freq # pylint: disable=protected-access
    }

class BasicSender(DefaultDevice):

    def __init__(self, part, engine, intensity, frequency,
                 frequency_err_gen=None, intensity_err_gen=None,
                 device_type='basic-sender'):
        super().__init__(device_type=device_type)

        self.__part = part
        self.__engine = engine
        self.__int_err_gen = intensity_err_gen
        self.__freq_err_gen = frequency_err_gen
        self._frequency = frequency
        self._intensity = intensity

    def act(self):
        pass

    def send(self):

        if self.__freq_err_gen is None:
            frequency = self._frequency
        else:
            frequency = abs(self.__freq_err_gen(self._frequency))

        if self.__int_err_gen is None:
            intensity = self._intensity
        else:
            intensity = abs(self.__int_err_gen(self._intensity))

        self.__engine.newSignal(self.__part.position, intensity, frequency)

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, BasicSender.__COMMANDS, *args)

    __COMMANDS = {
        'get-frequency': lambda self: self._frequency, # pylint: disable=protected-access
        'get-intensity': lambda self: self._intensity, # pylint: disable=protected-access
        'send-signal': send
    }

class ConfigurableSender(BasicSender):

    def __init__(self, *args, min_frequency=0, max_frequency=math.inf,
                 min_intensity=0, max_intensity=math.inf, **kwargs):
        super().__init__(*args, **kwargs, device_type='sender')

        self.__min_freq = min_frequency
        self.__max_freq = max_frequency
        self.__min_int = min_intensity
        self.__max_int = max_intensity

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, ConfigurableSender.__COMMANDS, *args)

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        if self.__min_freq <= self._frequency <= self.__max_freq:
            self._frequency = value

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, value):
        if self.__min_int <= self._intensity <= self.__max_int:
            self._intensity = value

    __COMMANDS = {
        'set-frequency': lambda self, val:
                         ConfigurableSender.frequency.fset(self, float(val)),
        'set-intensity': lambda self, val:
                         ConfigurableSender.intensity.fset(self, float(val)),
        'min-frequency': lambda self: self.__min_freq, # pylint: disable=protected-access
        'max-frequency': lambda self: self.__max_freq, # pylint: disable=protected-access
        'min-intensity': lambda self: self.__min_int, # pylint: disable=protected-access
        'max-intensity': lambda self: self.__max_int # pylint: disable=protected-access
    }
