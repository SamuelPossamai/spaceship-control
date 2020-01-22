
import os
from pathlib import Path

class FileInfo:

    __instance = None

    def __init__(self):
        self.__path = \
            Path.home().joinpath('.local/share/spaceshipcontrol').resolve()
        self.__dist_data_path = Path(__file__).parent.parent.resolve()

        if self.__dist_data_path.name == 'src':
            self.__dist_data_path = self.__dist_data_path.parent

        self.__path.mkdir(parents=True, exist_ok=True)

        create_n_link_example_dirs = ['controllers', 'ships', 'scenarios']

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

    def __new__(cls):
        if FileInfo.__instance is None:
            FileInfo.__instance = super().__new__(cls)

        return FileInfo.__instance

    def uiFilePath(self, *args, **kwargs):
        return self.__getPath(self.__dist_data_path.joinpath('forms'), *args,
                              **kwargs)

    def shipModelPath(self, *args, **kwargs):
        return self.__getPath(self.__path.joinpath('ships'), *args, **kwargs)

    def controllerPath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('controllers'), *args, **kwargs)

    def scenarioPath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('scenarios'), *args, **kwargs)

    @staticmethod
    def __getPath(basepath, name=None, to_string=True):

        if name is None:
            if to_string:
                return str(basepath)
            return basepath

        file_path = basepath.joinpath(name)

        if not(file_path.exists() and file_path.is_file()):
            return None

        if to_string:
            return str(file_path)
        return file_path