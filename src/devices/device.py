"""Base classes meant to represent a ship device.

This module contains classes that represent a ship device, some of these classes
are inherited by classes inside `structure.py` to represent a ship structure, a
sensor, an actuator or another device.
"""

import shlex

from abc import ABC, abstractmethod

class Device(ABC):
    """Base class for all devices.

    This abstract class is the base for all classes that represent a ship
    device.

    """

    @abstractmethod
    def act(self) -> None:
        """Method used to perform the device actions.

        This method is called perodically and is meant to be used to perform
        actions that are done over time.

        """
        pass

    @abstractmethod
    def communicate(self, input_: str) -> str:
        """Method used to communicate with the device controller.

        This method receive an input from the controller, do some action
        accordingly and gives back an answer.

        This method is used so the controller can modify the state of the
        device or get some information from it.

        Note:
            This method will be called inside a separeted thread so the
            implementation of this method cannot contain any instruction that
            need to be executed inside the main thread.

        Args:
            input_: The message sent to the device, it should'nt contain any
                control character.

        Returns:
            A string that contain no control characters.

        """
        pass

class DefaultDevice(Device):
    """Device that use shell-like command to communicate.

    This class represent a more concrete device than the 'Device' class, classes
    that inherits from this have a default way to return information that will
    help the controller to discover what the actions that it can perform.

    Note:
        This class implements `Device` communicate method and declare the method
        `command` to be used instead, but it should't be overriden without
        calling the this class `command` method.

    Args:
        device_type: String that represent what the device is meant to be,
            using this value consistently it will help the controller to now
            what the commands it can send to this device.
        device_desc: Description of what this device does in a human readable
            way.
        device_info: Dictionary that contains pair key, value that represents
            constants that may used to help the controller to know more
            information about this device.
    """

    def __init__(self, device_type: str = 'none',
                 device_desc: str = 'not specified',
                 device_info: 'Dict[str, str]' = None):

        self.__device_type = device_type
        self.__device_desc = device_desc

        if device_info is None:
            self.__device_info = {}
        else:
            self.__device_info = device_info.copy()

    def communicate(self, input_: str) -> str:
        """Method used to communicate with the device controller.

        This method receive an input from the controller, do some action
        accordingly and gives back an answer.

        This method is used so the controller can modify the state of the
        device or get some information from it.

        This method is implemented in a way that it will call the method
        `command`, tranform the return into a string and return it.

        Note:
            The input is considered invalid if it's not a shell-like command.

        Args:
            input_: The message sent to the device, it should'nt contain any
                control character and should be a formatted as a shell-like
                command.

        Returns:
            The return of the method `command` turned into a string that must
            contain no control characters or 'Invalid command' if the input
            is considered invalid.

        """

        try:
            return str(self.command(shlex.split(input_)))
        except Exception:
            return 'Invalid command'

    def setInfo(self, name: str, value: 'Optional[str]') -> None:
        """This method is used to create, modify or delete device info.

        This will create, delete or modify information that can be obtained
        by the process communicating with this device through the command
        `get-info <info_name>` where `<info_name>' is the parameter `name`.

        Args:
            name: Name of the information that will be set, if the value does
                not exist and the value is valid, the information will be added
                otherwise the value will be modified.
            value: Value of the information that will be set, if None is passed
                instead, the information with this name will be deleted.

        """

        if value is None:
            try:
                del self.__device_info[name]
            except KeyError:
                pass
        else:
            self.__device_info[name] = value

    def getInfo(self, name: str) -> 'Optional[str]':
        """This method is used to get device info.

        This method will return the info named `name` if it exists.

        Note:
            This method is called by the command `get-info <name>`.

        Args:
            name: The name of the information that will be returned.

        Returns:
            The value of the information if it exists, None otherwise.

        """

        return self.__device_info.get(name)

    def deviceType(self) -> str:
        """This method is used to get the device type.

        This method will return the device type of this device.

        Note:
            This method is called by the command `device-type`.

        Returns:
            This device type.

        """

        return self.__device_type

    def deviceDescription(self) -> str:
        """This method is used to get the device description.

        This method will return the description of this device.

        Note:
            This method is called by the command `device-desc`.

        Returns:
            This device description.

        """

        return self.__device_desc

    def __command(self, command: 'List[str]',
                  command_actions: 'Dict[str, Callable]') -> 'Any':

        if not command:
            return None

        command_func = command_actions.get(command[0])

        if command_func is None:
            return None

        try:
            command_args = iter(command)
            next(command_args)
            return command_func(self, *command_args)
        except Exception:
            return 'An error ocurred running the command'

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        """Method called by communicate that may be overriden.

        This method is used to handle communicate method and will be called
        if the input given to communicate is a valid shell-like command, this
        method will use the first element of `command` to locate a function
        that will be called passing the rest of the list as parameter.

        More arguments may be passed to be used to be looked upon for a command,
        that is not an original command.

        Note:
            This method should be called even if overriden, if you desire to
            add commands, use the variadic positional parameters.

        Args:
            command: List with the first argument being the command name and
                the rest as the arguments.
            *args: Dicionary containing pair string and callable that will where
                the command will be looked for if it was not found yet.

        Returns:
            'Invalid command' if the command is not found.
            'An error ocurred running the command' if an error occured running
                the command function.
            Otherwise it will return the result of the function that was called.

        """

        for command_actions in args:

            if command_actions is not None:

                result = self.__command(command, command_actions)
                if result is not None:
                    return result

        result = self.__command(command, DefaultDevice.__COMMANDS)

        if result is None:
            return 'Invalid command'

        return result

    __COMMANDS = {

        'device-type': deviceType,
        'device-desc': deviceDescription,
        'get-info': lambda self, name: self.getInfo(name) or '<<null>>'
    }

class DeviceGroup(DefaultDevice):

    def __init__(self, device_type: str = 'device-group', **kwargs):
        super().__init__(device_type=device_type, **kwargs)

        self.__device_list: 'List[Device]' = []
        self.__device_dict: 'Dict[str, Device]' = {}

        self.setInfo('is-device-group', 'yes')

    def addDevice(self, device: Device, name: str = None):

        self.__device_list.append(device)
        if name is not None:
            self.__device_dict[name] = device
            if isinstance(device, DefaultDevice):
                device.setInfo('device-name-in-group', name)

    def deviceCount(self):
        return len(self.__device_list)

    def act(self) -> None:
        for device in self.__device_list:
            device.act()

    def communicate(self, input_: str) -> str:

        sp_input = input_.split(':', 1)

        if len(sp_input) == 2:
            device_id = sp_input[0]
            try:
                device_number = int(device_id)
            except ValueError:
                device = self.__device_dict.get(device_id)
            else:
                if device_number < 0 or device_number >= self.deviceCount():
                    return f'Error: Invalid device \'{device_number}\''

                device = self.__device_list[device_number]

            if device is None:
                return 'Invalid device'

            return device.communicate(sp_input[1])

        return super().communicate(input_)

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, DeviceGroup.__COMMANDS)

    __COMMANDS = {

        'device-count': deviceCount
    }

class PropertyDevice(DefaultDevice):

    def __init__(self,
                 properties: 'Dict[str, property]' = None,
                 **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__properties = {} if properties is None else properties.copy()

    def getProperty(self, prop_name: str) -> 'Any':
        prop = self.__properties.get(prop_name)
        if prop is None:
            return '<<Unknown property>>'

        return prop.fget(self)

    def setProperty(self, prop_name: str, val: 'Any') -> 'Any':
        prop = self.__properties.get(prop_name)
        if prop is None:
            return '<<Unknown property>>'

        setter = prop.fset

        if setter is None:
            return '<<This property can\'t be set>>'

        setter(self, val)

        return '<<OK>>'

    def properties(self) -> 'Iterable[Tuple[str, Any]]':
        return self.__properties.items()

    def __listPropertiesStr(self) -> str:
        return ':'.join(key for key, _ in self.properties),

    def __showPropertiesStr(self) -> str:
        return ':'.join(f'{key}={val}' for key, val in self.properties)

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, PropertyDevice.__COMMANDS, *args)

    __COMMANDS = {

        'set-property': setProperty,
        'get-property': getProperty,
        'list-properties': __listPropertiesStr,
        'show-properties': __showPropertiesStr
    }
