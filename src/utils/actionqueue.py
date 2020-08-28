
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Callable, Any

class Action:

    def __init__(self, function: 'Callable', *args: 'Any') -> None:

        self.function = function
        self.args = args

class ActionQueue:

    def __init__(self) -> None:
        self.__list: 'List[Action]' = []
        self.__lock = Lock()

    def add(self, action: Action) -> None:
        with self.__lock:
            self.__list.append(action)

    def processItems(self) -> None:
        with self.__lock:
            for action in self.__list:
                action.function(*action.args)
