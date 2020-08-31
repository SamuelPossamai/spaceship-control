
from typing import TYPE_CHECKING, cast as typingcast

from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QStandardItemModel, QStandardItem

if TYPE_CHECKING:
    from typing import Sequence, List, Optional
    import anytree
    from PyQt5.QtWidgets import QWidget

class NodeValue:

    def __init__(self, name: str, description: 'Optional[str]',
                 label: str = None) -> None:
        self.__name = name
        self.__desc = description
        self.__item = None
        self.__label = label

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, new_val: str) -> None:
        self.__name = new_val
        if self.__label is None and self.__item is not None:
            self.__item.setText(new_val)

    @property
    def label(self) -> 'Optional[str]':
        if self.__label is None:
            return self.__name
        return self.__label

    @label.setter
    def label(self, new_val: 'Optional[str]') -> None:
        self.__label = new_val
        if self.__item is not None:
            if self.__label is None:
                self.__item.setText(self.__name)
            else:
                self.__item.setText(self.__label)

    @property
    def description(self) -> 'Optional[str]':
        return self.__desc

    @description.setter
    def description(self, new_val: 'Optional[str]') -> None:
        self.__desc = new_val
        if self.__item is not None:
            self.__item.setToolTip(new_val)

    def __setItem(self, new_val: 'QStandardItem') -> None:
        self.__item = new_val

    item = property(None, __setItem)

class NodeTreeView(QTreeView):

    def __init__(self, parent: 'QWidget' = None) -> None:

        super().__init__(parent=parent)

        self.setModel(QStandardItemModel())
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)

    def clear(self) -> None:
        self.model().clear()

    def addNodes(self, nodes: 'Sequence[anytree.Node]') -> None:

        for node in nodes:
            NodeTreeView.__addNode(self.model(), node)

    def selectedItem(self) -> 'QStandardItem':
        return self.model().itemFromIndex(self.currentIndex())

    def selectedIsLeaf(self) -> bool:
        return typingcast(bool, self.selectedItem().rowCount() == 0)

    def selectedItemPath(self) -> 'Sequence[QStandardItem]':
        current_item = self.selectedItem()

        result: 'List[QStandardItem]' = []
        while current_item is not None:
            result.insert(0, current_item)
            current_item = current_item.parent()

        return result

    @staticmethod
    def __addNode(parent_row: 'QStandardItem',
                  options: 'anytree.Node') -> None:

        node_value = options.name
        set_item = False

        if isinstance(node_value, NodeValue):
            set_item = True
            node_desc = node_value.description
            node_name = node_value.name
            node_label = node_value.label
        elif isinstance(node_value, tuple):
            node_desc = node_value[1]
            node_name = node_value[0]
            node_label = node_name
        else:
            node_name = node_value
            node_label = node_name
            node_desc = None

        item = QStandardItem(node_label)
        item.setData(node_name)

        if node_desc:
            item.setToolTip(node_desc)
        item.setEditable(False)
        parent_row.appendRow(item)

        for child in options.children:
            NodeTreeView.__addNode(item, child)

        if set_item is True:
            node_value.item = item
