
import sys
from pathlib import Path

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

# pylint: disable=relative-beyond-top-level

from ..storage.fileinfo import FileInfo

# pylint: enable=relative-beyond-top-level

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))
UiChooseFromTree, _ = FileInfo().loadUi('choosefromtree.ui') # pylint: disable=invalid-name
sys.path.pop(0)

class ChooseFromTreeDialog(QDialog):

    def __init__(self, options: 'Sequence[anytree.Node]',
                 parent: 'QWidget' = None) -> None:

        super().__init__(parent=parent)

        self.__ui = UiChooseFromTree()
        self.__ui.setupUi(self)

        self.__ui.treeView.addNodes(options)

        self.__result = None

        self.__ui.buttonBox.accepted.connect(self.__dialogAccepted)
        self.__ui.treeView.clicked.connect(self.__treeViewClicked)

    def getOption(self):
        self.__result = None
        self.exec_()
        return self.__result

    def __dialogAccepted(self):
        self.__result = tuple(
            item.data() for item in self.__ui.treeView.selectedItemPath())

    def __treeViewClicked(self):

        self.__ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            self.__ui.treeView.selectedIsLeaf())
