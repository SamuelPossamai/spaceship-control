
from abc import ABC, abstractmethod

class CustomLoader(ABC):

    def __init__(self, create_functions_base, label='Model') -> None:
        self.__label = label
        self.__create_functions_base = create_functions_base
        self._load_functions = create_functions_base.copy()

    def clearCustoms(self) -> None:
        self._load_functions = self.__create_functions_base.copy()

    def _getTypes(self, config): # pylint: disable=no-self-use
        return (config.get('type'),)

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

        model_types = self._getTypes(config)
        if model_types is None:
            raise Exception('{self.__label} type is required')

        for type_ in model_types:
            if type_ in self._load_functions:
                raise Exception(f'{self.__label} type \'{type_}\''
                                ' already in use')

            self._addCustom(config, type_, model_info)
