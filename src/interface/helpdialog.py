
import sys
from pathlib import Path

from PyQt5.QtWidgets import QDialog

# pylint: disable=relative-beyond-top-level

from ..storage.fileinfo import FileInfo

# pylint: enable=relative-beyond-top-level

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))
UiHelpWidget, _ = FileInfo().loadUi('helpwindow.ui') # pylint: disable=invalid-name
sys.path.pop(0)

class HelpDialog(QDialog):

    def __init__(self, parent: 'QWidget' = None) -> None:

        super().__init__(parent=parent)

        self.__ui = UiHelpWidget()
        self.__ui.setupUi(self)

        self.__ui.treeView.addNodes(FileInfo().listFilesTree(
            FileInfo.FileDataType.HANDBOOK).children)
