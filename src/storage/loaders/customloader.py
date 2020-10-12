
from abc import ABC, abstractmethod

class CustomLoader(ABC):

    def __init__(self, create_functions_base, label='Model') -> None:
        self.__label = label
        self.__create_functions_base = create_functions_base
        self._load_functions = create_functions_base.copy()

    def clearCustoms(self) -> None:
        self._load_functions = self.__create_functions_base.copy()

    def _getType(self, config): # pylint: disable=no-self-use
        return config.get('type')

    @abstractmethod
    def _addCustom(self, config, model_type, model_info):
        pass

    def addCustom(self, custom_model_info):

        config = custom_model_info.get('Configuration')

        if config is None:
            raise Exception(f'{self.__label} \'Configuration\' is required')

        model_info = custom_model_info.get('ModelInfo')

        if model_info is None:
            raise Exception('{self.__label} \'ModelInfo\' is required')

        model_type = self._getType(config)
        if model_type is None:
            raise Exception('{self.__label} type is required')

        if model_type in self._load_functions:
            raise Exception(f'{self.__label} type \'{model_type}\''
                            ' already in use')

        return self._addCustom(config, model_type, model_info)
