
import os
import sys
import shutil
from pathlib import Path
import subprocess
from enum import Enum, Flag, auto as flagAuto
from typing import NamedTuple
from fnmatch import fnmatch
from typing import TYPE_CHECKING, cast as typingcast

import json
import toml
import yaml

from PyQt5 import uic

from anytree import Node

from . import configfileinheritance, configfilevariables

from .loaders import (
    shiploader, scenarioloader, controllerloader, objectloader
)

from ..utils import dictutils

# sys.path manipulation so it is not imported in a different path
sys.path.insert(0, str(Path(__file__).parent.parent.joinpath('interface')))
from nodetreeview import NodeValue # pylint: disable=wrong-import-order, wrong-import-position, import-error
sys.path.pop(0)

if TYPE_CHECKING:
    from typing import (
        Sequence, Optional, Union, List, Any, Callable, Dict, MutableMapping
    )

class _FileInfo_FileMetadataType(Flag):
    ABSENT = 0
    FILE_INTERNAL = flagAuto()
    FILE_EXTERNAL = flagAuto()
    DIRECTORY = flagAuto()
    CONF_FILE_DEFAULT = FILE_INTERNAL | DIRECTORY
    GENERIC_FILE_DEFAULT = FILE_EXTERNAL | DIRECTORY

class FileInfo:

    __instance: 'Optional[FileInfo]' = None

    FileDataType = Enum('FileDataType', ('CONTROLLER', 'SHIPMODEL', 'SCENARIO',
                                         'OBJECTMODEL', 'IMAGE', 'UIDESIGN',
                                         'HANDBOOK', 'METADATA'))

    FileMetadataType = _FileInfo_FileMetadataType

    class __DataTypeInfoType(NamedTuple):
        path: str
        use_dist_path: bool = False
        suffix_list: 'Optional[Sequence[str]]' = None
        list_remove_suffix: bool = False
        list_blacklist: 'Sequence[str]' = ()
        package_glob_list: 'Optional[Sequence[str]]' = None
        files_mode: 'Optional[int]' = None
        metadata_type: '_FileInfo_FileMetadataType' \
            = _FileInfo_FileMetadataType.ABSENT
        use_root_path: bool = False

    __CONF_FILE_SUFFIX_LIST = ('.toml', '.json', '.yaml', '.yml')
    __CONF_FILE_GLOB_LIST = tuple(
        f'*{suffix}' for suffix in __CONF_FILE_SUFFIX_LIST)

    __DATA_TYPE_INFO = {
        FileDataType.CONTROLLER: __DataTypeInfoType(
            'controllers', False, None, False, ('__pycache__',), ('*',), 0o555,
            metadata_type=FileMetadataType.GENERIC_FILE_DEFAULT),
        FileDataType.SHIPMODEL: __DataTypeInfoType(
            'ships', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644,
            metadata_type=FileMetadataType.CONF_FILE_DEFAULT),
        FileDataType.SCENARIO: __DataTypeInfoType(
            'scenarios', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644,
            metadata_type=FileMetadataType.CONF_FILE_DEFAULT),
        FileDataType.OBJECTMODEL: __DataTypeInfoType(
            'objects', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644,
            metadata_type=FileMetadataType.CONF_FILE_DEFAULT),
        FileDataType.IMAGE: __DataTypeInfoType(
            'images', False, None, False, (),
            ('*.gif', '*.png'), 0o644,
            metadata_type=FileMetadataType.ABSENT),
        FileDataType.UIDESIGN: __DataTypeInfoType(
            'forms', True, ('.ui',), True, (), None, None,
            metadata_type=FileMetadataType.ABSENT),
        FileDataType.HANDBOOK: __DataTypeInfoType(
            'docs/handbook', True, ('*.toml',), True, (), None, None,
            metadata_type=FileMetadataType.CONF_FILE_DEFAULT),
        FileDataType.METADATA: __DataTypeInfoType(
            '/', False, __CONF_FILE_SUFFIX_LIST, True, (),
            None, None, metadata_type=FileMetadataType.ABSENT,
            use_root_path=True),
    }

    def __init__(self) -> None:

        self.__already_initialized: bool
        if self.__already_initialized: # pylint: disable=access-member-before-definition
            return

        self.__already_initialized = True

        self.__statistics_file: 'Optional[Union[str, Path]]' = None

        self.__path = \
            Path.home().joinpath('.local/share/spaceshipcontrol').resolve()
        self.__dist_data_path = Path(__file__).parent.parent.resolve()
        self.__config_file_path = Path.home().joinpath(
            '.config/spaceshipcontrol/config.toml').resolve()

        if self.__dist_data_path.name == 'src':
            self.__dist_data_path = self.__dist_data_path.parent

        self.__path.mkdir(parents=True, exist_ok=True)
        self.__config_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.__config_content = toml.load(self.__config_file_path)
        except FileNotFoundError:
            self.__config_content = {}

        create_n_link_example_dirs = ['controllers', 'ships', 'scenarios',
                                      'objects', 'images']

        dist_data_examples_path = self.__dist_data_path.joinpath('examples')

        for dirname in create_n_link_example_dirs:
            path = self.__path.joinpath(dirname)
            path.mkdir(exist_ok=True)

            example_dir_path = path.joinpath('examples')
            try:
                os.unlink(example_dir_path)
            except FileNotFoundError:
                pass
            os.symlink(dist_data_examples_path.joinpath(dirname),
                       example_dir_path)

    def __new__(cls) -> 'FileInfo':

        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__already_initialized = False

        return cls.__instance

    def readConfig(self, *args: 'Any', default: 'Any' = None,
                   value_type: 'Callable' = None) -> 'Any':
        current = self.__config_content
        for arg in args:
            if isinstance(current, dict):
                current = typingcast('Dict[str, Any]', current.get(arg))
                if current is None:
                    return default
            else:
                return default

        if value_type is not None:
            try:
                return value_type(current)
            except Exception:
                return default

        return current

    def writeConfig(self, value: 'Any', *args: 'Any') -> None:

        if not args:
            raise Exception('FileInfo.writeConfig: Path must be specified')

        previous = None
        current = self.__config_content

        for arg in args:
            new_current = current.get(arg)
            if not isinstance(new_current, dict):
                new_current = current[arg] = {}

            previous = current
            current = new_current

        if previous is not None:
            previous[args[-1]] = value

    def saveConfig(self) -> None:

        with open(self.__config_file_path, 'w') as file:
            toml.dump(self.__config_content, file)

    def listFilesTree(self, filedatatype: 'FileDataType',
                      use_metadata: bool = True,
                      show_meta_files: bool = False,
                      show_hidden_files: bool = False) -> 'Optional[Node]':

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        blacklist_tmp: 'List[str]' = []
        if use_metadata:
            metadata_type = filedatatype_info.metadata_type

            if show_meta_files is False:
                if metadata_type & self.FileMetadataType.DIRECTORY:
                    blacklist_tmp.append('__metadata__.*')

                if metadata_type & self.FileMetadataType.FILE_EXTERNAL:
                    blacklist_tmp.append('*.__metadata__.*')
        else:
            metadata_type = self.FileMetadataType.ABSENT

        blacklist: 'Sequence[str]'
        if blacklist_tmp:
            blacklist_tmp.extend(filedatatype_info.list_blacklist)
            blacklist = blacklist_tmp
        else:
            blacklist = filedatatype_info.list_blacklist

        path = self.getPath(filedatatype)

        if path is None:
            return None

        return self.__listTree(
            path,
            Node(filedatatype_info.path),
            remove_suffix=filedatatype_info.list_remove_suffix,
            blacklist=blacklist,
            metadata_type=metadata_type,
            can_hide_files=not show_hidden_files)

    @property
    def statistics_filepath(self) -> 'Optional[Union[str, Path]]':
        return self.__statistics_file

    @statistics_filepath.setter
    def statistics_filepath(
        self, filepath: 'Optional[Union[str, Path]]') -> None:

        self.__statistics_file = filepath

    def saveStatistics(self, statistics: 'Dict[str, Any]') -> None:

        if self.__statistics_file is None:
            return

        with open(self.__statistics_file, 'w') as file:
            yaml.dump(statistics, file)

    def getHandbookText(self, section: str) -> str:

        content = self.__getContent(section, self.FileDataType.HANDBOOK)

        if content is None:
            return ''

        paragraphs = content.get('Paragraph', ())

        if paragraphs:
            return '\n'.join(
                paragraph.get('content', '') for paragraph in paragraphs)

        return ''

    def __readMetadata(self, path: 'Path',
                       metadata_type: '_FileInfo_FileMetadataType',
                       is_directory: bool) -> 'Optional[Any]':

        if is_directory:
            if metadata_type & self.FileMetadataType.DIRECTORY:
                try:
                    return self.__getContent(str(path.joinpath('__metadata__')),
                                             self.FileDataType.METADATA)
                except Exception:
                    pass
        else:
            if metadata_type & self.FileMetadataType.FILE_INTERNAL:
                try:
                    content = self.__getContent(
                        str(path), self.FileDataType.METADATA,
                        suffix_specified=True)
                except Exception:
                    pass
                else:
                    if content is not None and 'Metadata' in content:
                        return content['Metadata']

            if metadata_type & self.FileMetadataType.FILE_EXTERNAL:

                external_file_path = path.with_suffix(
                    ''.join(path.suffixes) + '.__metadata__')
                try:
                    content = self.__getContent(
                        str(external_file_path), self.FileDataType.METADATA)
                except Exception:
                    pass
                else:
                    if content is not None:
                        return content

        return None

    def __listTree(self, base_path: 'Path', current_node: 'Node',
                   blacklist: 'Sequence[str]' = (), remove_suffix: bool = True,
                   metadata_type: '_FileInfo_FileMetadataType' = None,
                   can_hide_files: bool = True) -> 'Node':

        for path in sorted(base_path.iterdir()):
            is_directory = path.is_dir()

            if any(fnmatch(path.name, match_str) for match_str in blacklist):
                continue

            original_path = path

            if remove_suffix is True:
                path = path.with_suffix('')

            name = path.name

            if metadata_type is not None:
                metadata = self.__readMetadata(
                    original_path, metadata_type, is_directory)

                if metadata:
                    if can_hide_files and metadata.get('hide', False):
                        continue

                    label = str(metadata.get('name', name))
                    desc = metadata.get('description', '')
                    if desc is not None:
                        name = NodeValue(name, str(desc), label=label)

            new_node = Node(name, parent=current_node)
            if is_directory:
                self.__listTree(path, new_node, blacklist=blacklist,
                                remove_suffix=remove_suffix,
                                metadata_type=metadata_type,
                                can_hide_files=can_hide_files)
                if not new_node.children:
                    new_node.parent = None

        return current_node

    def addFiles(self, filedatatype: 'FileDataType',
                 files: 'List[str]') -> bool:

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        if filedatatype_info.files_mode is None:
            raise ValueError('Can\'t add files to this FileDataType')

        path = self.getPath(filedatatype)

        if path is None:
            return False

        self.__addFiles(path, files,
                        mode=filedatatype_info.files_mode)
        return True

    def addPackage(self, package_pathname: str) -> None:

        package_path = Path(package_pathname)

        package_name = package_path.name

        for directory, mode, patterns in (
                ('scenarios', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('ships', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('objects', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('controllers', 0o555, ('*',)),
                ('images', 0o644, ('*.png', '*.gif'))):

            dest_base_path = self.__path.joinpath(directory).joinpath(
                package_name)
            package_subdir_path = package_path.joinpath(directory)

            for pat in patterns:
                for path in package_subdir_path.rglob(pat):
                    if path.is_file():

                        dest_path = dest_base_path.joinpath(
                            path.parent.relative_to(package_subdir_path))

                        if not dest_path.exists():
                            dest_path.mkdir(parents=True)

                        self.__addFiles(dest_path, (path,), mode=mode)

    def __findSuffix(self, basename, filedatatype, valid_suffixes):

        for valid_suffix in valid_suffixes:
            filepath = self.getPath(filedatatype, basename + valid_suffix)
            if filepath is not None:
                return filepath, valid_suffix

        return None, None

    def __getContent(self, basename: str, filedatatype: 'FileDataType',
                     inexistent_message: 'Optional[str]' = None,
                     suffix_specified: bool = False) \
                         -> 'Optional[MutableMapping[str, Any]]':

        if suffix_specified:
            filepath = self.getPath(filedatatype, basename)
            suffix = Path(basename).suffix
        else:
            filepath, suffix = self.__findSuffix(
                basename, filedatatype, ('.toml', '.json', '.yaml', '.yml'))

        if filepath is None:
            if inexistent_message is None:
                return None
            raise Exception(inexistent_message.format(name=basename))

        if suffix == '.json':
            with open(filepath) as file:
                return json.load(file)

        if suffix in ('.yaml', '.yml'):
            with open(filepath) as file:
                return yaml.safe_load(file)

        return toml.load(filepath)

    def __getScenarioContent(self, scenario_name: str) \
        -> 'Optional[MutableMapping[str, Any]]':

        content = self.__getContent(scenario_name, self.FileDataType.SCENARIO,
                                    'Inexistent scenario named \'{name}\'')

        if content is None:
            return None

        dictutils.mergeMatch(content, (), ('Ship', 'ships'), 'Ship',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Objective', 'objectives'),
                             'Objective', absolute=True)

        configfilevariables.subVariables(content)

        return content

    def __getShipContent(self, ship_model: str,
                         variables: 'Dict[str, Any]' = None) \
                             -> 'Optional[MutableMapping[str, Any]]':

        content = self.__getContent(ship_model, self.FileDataType.SHIPMODEL,
                                    'Inexistent ship model named \'{name}\'')

        if content is None:
            return None

        dictutils.mergeMatch(content, (), ('Shape', 'shapes'), 'Shape',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Actuator', 'actuators'), 'Actuator',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Sensor', 'sensors'), 'Sensor',
                             absolute=True)
        dictutils.mergeMatch(content, (),
                             ('InterfaceDevice', 'interface_devices'),
                             'InterfaceDevice',
                             absolute=True)
        dictutils.mergeMatch(content, ('Shape',), ('Point', 'points'), 'Point',
                             absolute=True)

        configfilevariables.subVariables(content, variables=variables)

        return content

    def __getObjectContent(self, object_model: str,
                           variables: 'Dict[str, Any]' = None) \
                               -> 'Optional[MutableMapping[str, Any]]':

        content = self.__getContent(object_model, self.FileDataType.OBJECTMODEL,
                                    'Inexistent object model named \'{name}\'')

        if content is None:
            return None

        dictutils.mergeMatch(content, (), ('Shape', 'shapes'), 'Shape',
                             absolute=True)
        dictutils.mergeMatch(content, ('Shape',), ('Point', 'points'), 'Point',
                             absolute=True)

        configfilevariables.subVariables(content, variables=variables)

        return content

    def loadUi(self, filename: str):
        return uic.loadUiType(
            self.getPath(self.FileDataType.UIDESIGN, filename))

    def loadScenario(self, scenario_name: str):

        prefixes = scenario_name.split('/')[:-1]

        scenario_content = self.__getScenarioContent(scenario_name)

        if scenario_content is None:
            return None

        scenario_content = configfileinheritance.mergeInheritedFiles(
            scenario_content, self.__getScenarioContent, prefixes=prefixes)

        return scenarioloader.loadScenario(scenario_content, prefixes=prefixes)

    def loadShip(self, model, name, space, communication_engine=None,
                 variables=None):

        prefixes = model.split('/')[:-1]

        ship_content = self.__getShipContent(model, variables=variables)

        ship_content = configfileinheritance.mergeInheritedFiles(
            ship_content, self.__getShipContent, prefixes=prefixes)

        return shiploader.loadShip(ship_content, name, space, prefixes=prefixes,
                                   communication_engine=communication_engine)

    def loadObject(self, model, space, variables=None):

        prefixes = model.split('/')[:-1]

        obj_content = self.__getObjectContent(model, variables=variables)

        obj_content = configfileinheritance.mergeInheritedFiles(
            obj_content, self.__getObjectContent, prefixes=prefixes)

        return objectloader.loadObject(obj_content, space, prefixes=prefixes)

    def loadController(self, controller_name, ship, json_info,
                       debug_queue, lock):
        return controllerloader.loadController(
            self.getPath(self.FileDataType.CONTROLLER, controller_name),
            ship, json_info, debug_queue, lock)

    def openFile(self, filedatatype: 'FileDataType', filename: str) -> None:

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        valid_suffixes = filedatatype_info.suffix_list

        if valid_suffixes is None:
            path = self.getPath(filedatatype, filename)
        else:
            path, _ = self.__findSuffix(filename, filedatatype, valid_suffixes)

        if path is not None:
            self.__openFile(str(path))

    @staticmethod
    def __openFile(path: str) -> None:
        subprocess.call(['xdg-open', path])

    @staticmethod
    def __addFiles(path: 'Union[str, Path]',
                   files: 'Sequence[Union[str, Path]]',
                   mode: int = 0o644) -> None:
        path_str = str(path)
        for filepath in files:
            new_file = shutil.copy(str(filepath), path_str)
            os.chmod(new_file, mode)

    def getPath(self, filedatatype: 'FileDataType',
                name: str = None) -> 'Optional[Path]':

        if filedatatype is None:
            return self.__path

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        if filedatatype_info.use_root_path:
            basepath = Path('/')
        elif filedatatype_info.use_dist_path:
            basepath = self.__dist_data_path
        else:
            basepath = self.__path

        filepath = basepath.joinpath(filedatatype_info.path)

        if name is None:
            return filepath

        filepath = filepath.joinpath(name)

        if not(filepath.exists() and filepath.is_file()):
            return None

        return filepath

    @staticmethod
    def __getFileDataTypeInfo(
        filedatatype: 'FileDataType') -> '__DataTypeInfoType':

        info = FileInfo.__DATA_TYPE_INFO.get(filedatatype)

        if info is None:
            raise ValueError(f'Invalid file data type')

        return info
