
import sys
import time
from math import pi
from threading import Lock
import traceback
from pathlib import Path
from queue import Empty as EmptyQueueException
from typing import TYPE_CHECKING, cast as typingcast

from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QTextBrowser
)
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QTimer, Qt

import pymunk

import anytree

from .choosefromtreedialog import ChooseFromTreeDialog
from .helpdialog import HelpDialog
from .loadgraphicitem import loadGraphicItem
from .loadship import loadShip
from .graphicsscene import GraphicsScene

from ..storage.fileinfo import FileInfo

from ..objectives.objective import createObjectiveTree

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))

# imported here so it is not imported in a different path

from nodetreeview import NodeValue # pylint: disable=wrong-import-order, wrong-import-position
UiMainWindow, _ = FileInfo().loadUi('mainwindow.ui') # pylint: disable=invalid-name
sys.path.pop(0)

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    from typing import Tuple, Any, Dict, Optional, List, Sequence
    from PyQt5.QtWidgets import QGraphicsItem, QWidget
    from PyQt5.QtGui import QKeyEvent, QMoveEvent, QResizeEvent, QCloseEvent
    from .loadship import ShipInterfaceInfo, SimpleQueue
    from .conditiongraphicspixmapitem import ConditionGraphicsPixmapItem
    from ..objectives.objective import Objective
    from ..devices.structure import Structure
    from ..devices.communicationdevices import CommunicationEngine
    from ..storage.loaders.scenarioloader import (
        ScenarioInfo, ShipInfo, ObjectInfo
    )
    from ..storage.loaders.imageloader import ImageInfo
    # pylint: enable=ungrouped-imports

class ObjectiveNodeValue(NodeValue):

    def __init__(self, objective: 'Objective') -> None:
        super().__init__(objective.name, objective.description)

        self.__objective = objective

    def update(self) -> None:
        if self.__objective.accomplished():
            symbol = '✓ '
        elif self.__objective.failed():
            symbol = '✗ '
        else:
            symbol = ''
        self.name = f'{symbol}{self.__objective.name}'

class MainWindow(QMainWindow):

    def __init__(self, parent: 'QWidget' = None, one_shot: bool = False,
                 time_limit: float = None, follow_ship: int = None,
                 start_zoom: float = None, timer_interval: int = 100) -> None:

        super().__init__(parent=parent)

        self.__ui = UiMainWindow()
        self.__ui.setupUi(self)

        self.__ui.view.setScene(GraphicsScene(parent))

        self.__lock = Lock()

        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__timerTimeout)

        self.__timer.setInterval(timer_interval)
        self.__timer.start()

        self.__space = pymunk.Space()
        self.__space.gravity = (0, 0)

        self.__ships: 'List[ShipInterfaceInfo]' = []
        self.__objects: 'List[Tuple[pymunk.Body, QGraphicsItem]]' = []
        self.__scenario_objectives: 'List[Objective]' = []
        self.__objectives_result: 'Optional[bool]' = None
        self.__current_scenario: 'Optional[str]' = None

        self.__widgets: 'List[QWidget]' = []
        self.__objectives_node_value: 'List[ObjectiveNodeValue]' = []

        self.__title_basename = 'Spaceship Control'

        view_geometry = self.__ui.view.geometry()
        view_geometry.setWidth(self.geometry().width()//2)
        self.__ui.view.setGeometry(view_geometry)
        self.__updateTitle()

        self.__current_ship_widgets_index = 0

        self.__comm_engine: 'Optional[CommunicationEngine]' = None
        self.__debug_msg_queues: 'Dict[str, SimpleQueue]' = {}

        self.__debug_messages_text_browsers: 'Dict[str, QTextBrowser]' = {}
        self.__condition_graphic_items: 'List[ConditionGraphicsPixmapItem]' = []

        self.__ship_to_follow = follow_ship

        self.__one_shot = one_shot
        self.__start_scenario_time: float = 0
        self.__time_limit = time_limit

        self.__ui.actionSimulationAutoRestart.setChecked(bool(
            FileInfo().readConfig('Simulation', 'auto_restart', default=False)))

        self.__ui.actionFitAllOnStart.setChecked(bool(
            FileInfo().readConfig('Simulation', 'fit_all_on_start',
                                  default=False)))

        self.__initConnections()

        self.setGeometry(
            FileInfo().readConfig('Window', 'x', default=self.x()),
            FileInfo().readConfig('Window', 'y', default=self.y()),
            FileInfo().readConfig('Window', 'width', default=self.width()),
            FileInfo().readConfig('Window', 'height', default=self.height()))

        self.__center_view_on = None

        self.__ui.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__ui.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__ui.view.setFocusPolicy(Qt.NoFocus)
        self.__ui.treeView.setFocusPolicy(Qt.NoFocus)

        self.setFocusPolicy(Qt.StrongFocus)

        big_int = 2**30
        self.__ui.view.scene().setSceneRect(-big_int, -big_int,
                                            2*big_int, 2*big_int)

        if start_zoom is not None:
            self.__ui.view.scale(start_zoom, start_zoom)

        self.setFocus()

    def moveEvent(self, event: 'QMoveEvent') -> None: # pylint: disable=no-self-use
        FileInfo().writeConfig(event.pos().x(), 'Window', 'x')
        FileInfo().writeConfig(event.pos().y(), 'Window', 'y')
        FileInfo().saveConfig()

    def resizeEvent(self, event: 'QResizeEvent') -> None: # pylint: disable=no-self-use
        FileInfo().writeConfig(event.size().width(), 'Window', 'width')
        FileInfo().writeConfig(event.size().height(), 'Window', 'height')
        FileInfo().saveConfig()

    def __updateTitle(self) -> None:

        if self.__current_scenario is None:
            self.setWindowTitle(self.__title_basename)
        else:
            if not self.__scenario_objectives or \
                self.__objectives_result is None:

                suffix = ''
            elif self.__objectives_result is True:
                suffix = ' ✓'
            else:
                suffix = ' ✗'

            self.setWindowTitle(
                f'{self.__title_basename}({self.__current_scenario}){suffix}')

    def closeEvent(self, _event: 'QCloseEvent') -> None:
        self.clear()
        self.__ui.view.setScene(None)

    def clear(self) -> None:

        self.setWindowTitle(self.__title_basename)

        self.__ui.deviceInterfaceComboBox.clear()
        self.__ui.deviceInterfaceComponents.show()
        self.__ui.treeView.show()

        self.__start_scenario_time = 0
        self.__center_view_on = None

        with self.__lock:
            self.__space.remove(*self.__space.bodies, *self.__space.shapes)

            scene = self.__ui.view.scene()
            for ship_info in self.__ships:
                for widget in ship_info.widgets:
                    widget.setParent(None)

            for item in scene.items():
                scene.removeItem(item)

            self.__ships.clear()
            self.__objects.clear()
            self.__condition_graphic_items.clear()

        self.__current_scenario = None
        self.__current_ship_widgets_index = 0
        self.__updateTitle()

    @staticmethod
    def __getOptionDialog(title: str, options: 'Tuple[anytree.Node]') \
            -> 'Optional[Sequence[str]]':

        dialog = ChooseFromTreeDialog(options)
        dialog.setWindowTitle(title)

        return dialog.getOption()

    def __loadScenarioAction(self) -> None:

        tree = FileInfo().listFilesTree(FileInfo.FileDataType.SCENARIO)

        if tree is None:
            return

        scenario = self.__getOptionDialog(
            'Choose scenario', tree.children)

        if scenario is not None:
            self.loadScenario('/'.join(scenario))

    def __chooseShipDialog(self, ship_options: 'Tuple[anytree.Node]') \
            -> 'Optional[Sequence[str]]':
        return self.__getOptionDialog('Choose ship model', ship_options)

    def __chooseControllerDialog(self,
                                 controller_options: 'Tuple[anytree.Node]') \
                                     -> 'Optional[Sequence[str]]':

        return self.__getOptionDialog('Choose controller', controller_options)

    def __loadShip(self, ship_info: 'ShipInfo',
                   arg_scenario_info: 'Dict[str, Any]') \
                       -> 'Optional[ShipInterfaceInfo]':

        loaded_ship_info = loadShip(
            self.__space, ship_info, arg_scenario_info, self.__lock,
            ship_options_dialog=self.__chooseShipDialog,
            controller_options_dialog=self.__chooseControllerDialog,
            communication_engine=self.__comm_engine)

        if loaded_ship_info is None:
            return None

        self.__widgets = loaded_ship_info.widgets

        for widget in self.__widgets:
            widget.setParent(self.__ui.deviceInterfaceComponents)

        self.__debug_msg_queues[loaded_ship_info.device.name] = \
            loaded_ship_info.msg_queue

        self.__condition_graphic_items.extend(
            loaded_ship_info.condition_graphic_items)

        self.__ui.view.scene().addItem(loaded_ship_info.gitem)

        self.__ui.deviceInterfaceComboBox.addItem(
            f'{ship_info.name} ({ship_info.model})')

        loaded_ship_info.thread.start()

        return loaded_ship_info

    def __loadObject(self, obj_info: 'ObjectInfo', fileinfo: 'FileInfo') \
            -> 'Optional[Tuple[pymunk.Body, QGraphicsItem]]':

        obj_model = obj_info.model
        if obj_model is None:
            obj_tree = fileinfo.listFilesTree(FileInfo.FileDataType.OBJECTMODEL)

            if obj_tree is None:
                return None

            obj_model = self.__getOptionDialog('Choose object model',
                                               obj_tree.children)

            if obj_model is None:
                return None

            obj_model = '/'.join(obj_model)

        object_info = fileinfo.loadObject(obj_model, self.__space,
                                          variables=obj_info.variables)

        body = object_info.body

        body.position = obj_info.position
        body.angle = obj_info.angle

        object_gitem, condition_graphic_items = loadGraphicItem(
            body.shapes, object_info.images, default_color=Qt.gray)

        self.__condition_graphic_items.extend(condition_graphic_items)

        self.__ui.view.scene().addItem(object_gitem)

        return body, object_gitem

    def __loadScenarioShips(self, ships_info: 'List[ShipInfo]',
                            arg_scenario_info: 'Dict[str, Any]') \
                                -> 'Optional[List[ShipInterfaceInfo]]':

        ships: 'List[Optional[ShipInterfaceInfo]]' = [None]*len(ships_info)
        for i, ship_info in enumerate(ships_info):
            try:
                ship = self.__loadShip(ship_info, arg_scenario_info.copy())
            except Exception as err:
                traceback.print_exc()
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading a ship({ship_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return None

            if ship is None:
                self.clear()
                return None

            ships[i] = ship

        ships_after = typingcast('List[ShipInterfaceInfo]', ships)

        if self.__ship_to_follow is not None:
            try:
                ship_item = ships_after[self.__ship_to_follow].gitem
            except IndexError:
                pass
            else:
                self.__ui.view.centerOn(ship_item.pos())
                self.__center_view_on = ship_item

        return ships_after

    def __loadScenarioObjects(self, objects_info: 'List[ObjectInfo]') \
            -> 'Optional[List[Tuple[pymunk.Body, QGraphicsItem]]]':

        objects: 'List[Optional[Tuple[pymunk.Body, QGraphicsItem]]]' = \
            [None]*len(objects_info)

        for i, obj_info in enumerate(objects_info):
            try:
                obj = self.__loadObject(obj_info, FileInfo())
            except Exception as err:
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading an object({obj_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return None

            objects[i] = obj

        return typingcast('List[Tuple[pymunk.Body, QGraphicsItem]]', objects)

    def __loadStaticImages(self, static_images: 'List[ImageInfo]') -> None:

        if static_images:
            for image_info in static_images:
                image_item, condition_graphic_items = loadGraphicItem(
                    None, (image_info,), group_z_value=-1)

                self.__condition_graphic_items.extend(condition_graphic_items)

                self.__ui.view.scene().addItem(image_item)

    def __loadDebugMessages(self, ships: 'List[ShipInterfaceInfo]') -> None:

        self.__ui.debugMessagesTabWidget.clear()
        self.__debug_messages_text_browsers.clear()
        for ship_info in ships:
            ship = ship_info.device

            tbrowser = QTextBrowser()
            self.__debug_messages_text_browsers[ship.name] = tbrowser
            self.__ui.debugMessagesTabWidget.addTab(tbrowser, ship.name)

    def __loadSpaceProperties(self, scenario_info: 'ScenarioInfo') -> None:

        space_info = scenario_info.physics_engine
        self.__space.damping = space_info.damping
        self.__space.gravity = space_info.gravity
        self.__space.collision_slop = space_info.collision_slop
        self.__space.collision_persistence = space_info.collision_persistence
        self.__space.iterations = space_info.iterations

    def loadScenario(self, scenario: str) -> None:

        self.clear()

        fileinfo = FileInfo()
        self.__start_scenario_time = time.time()

        try:
            scenario_info = fileinfo.loadScenario(scenario)
        except Exception as err:
            QMessageBox.warning(self, 'Error', (
                'An error occurred loading the scenario: \n'
                f'{type(err).__name__}: {err}'))
            return

        self.__ui.view.scene().setImage(
            QImage(str(FileInfo().getPath(FileInfo.FileDataType.IMAGE,
                                          scenario_info.background.image))))

        self.__loadSpaceProperties(scenario_info)

        self.__ui.deviceInterfaceWidgets.setVisible(
            scenario_info.visible_user_interface)
        self.__ui.debugMessagesTabWidget.setVisible(
            scenario_info.visible_debug_window)

        self.__comm_engine = scenario_info.communication_engine

        self.__scenario_objectives = scenario_info.objectives

        arg_scenario_info = {

            'objectives': [objective.toDict() for objective in
                           self.__scenario_objectives]
        }

        self.__debug_msg_queues.clear()

        ships = self.__loadScenarioShips(scenario_info.ships, arg_scenario_info)
        if ships is None:
            return

        objects = self.__loadScenarioObjects(scenario_info.objects)
        if objects is None:
            return

        self.__ships = ships
        self.__objects = objects

        self.__space.reindex_static()

        if self.__ships:
            for widget in self.__ships[0].widgets:
                widget.show()

        self.__objectives_node_value = []
        if self.__scenario_objectives:
            objectives_root_node = anytree.Node('root')
            for objective in self.__scenario_objectives:
                createObjectiveTree(objective, parent=objectives_root_node)

            for node in objectives_root_node.descendants:
                node_value = ObjectiveNodeValue(node.name)
                node.name = node_value
                self.__objectives_node_value.append(node_value)

            self.__ui.treeView.clear()
            self.__ui.treeView.addNodes(objectives_root_node.children)
        else:
            self.__ui.treeView.hide()

        self.__loadStaticImages(scenario_info.static_images)

        self.__current_scenario = scenario
        self.__ui.deviceInterfaceComboBox.setVisible(len(self.__ships) > 1)

        self.__loadDebugMessages(ships)

        if self.__ui.actionFitAllOnStart.isChecked():
            self.__timerTimeout()
            self.__ui.view.fitInView(
                self.__ui.view.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    @staticmethod
    def __updateGraphicsItem(body: 'pymunk.Body',
                             gitem: 'QGraphicsItem') -> None:

        pos = body.position
        gitem.setX(pos.x)
        gitem.setY(pos.y)
        gitem.prepareGeometryChange()
        gitem.setRotation(180*body.angle/pi)

    def __objectivesTimedOut(self) -> bool:

        if self.__time_limit is None or self.__start_scenario_time is None:
            return False

        return time.time() - self.__start_scenario_time > self.__time_limit

    def __createObjectivesRecord(self, node: 'anytree.Node',
                                 current_time: float) -> 'Dict[str, Any]':

        objective = node.name

        finished_at = objective.finished_at
        if finished_at is None:
            time_to_result = None
        else:
            time_to_result = finished_at - objective.started_at

        return {
            'name': objective.name,
            'desc': objective.description,
            'accomplished': objective.accomplished(),
            'failed': objective.failed(),
            'time': time_to_result,
            'children': [self.__createObjectivesRecord(child, current_time)
                         for child in node.children]
        }


    def __saveStatistics(self) -> None:

        current_time = time.time()
        scenario_time = current_time - self.__start_scenario_time

        if self.__time_limit is not None and scenario_time > self.__time_limit:
            scenario_time = self.__time_limit

        objectives = createObjectiveTree(self.__scenario_objectives)

        FileInfo().saveStatistics({
            'success': self.__objectives_result,
            'scenario': self.__current_scenario,
            'time': scenario_time,
            'objectives': [self.__createObjectivesRecord(child, current_time)
                           for child in objectives.children]
        })

    def __handleDebugMessages(self) -> None:

        for ship_name, queue in self.__debug_msg_queues.items():
            tbrowser = self.__debug_messages_text_browsers.get(ship_name)
            if tbrowser is None:
                continue

            try:
                while not queue.empty():
                    tbrowser.append(queue.get_nowait())
            except EmptyQueueException:
                pass

    def __checkObjectives(self, ships: 'Sequence[Structure]') -> None:

        objectives_complete = all(
            tuple(objective.verify(self.__space, ships)
                  for objective in self.__scenario_objectives))

        if objectives_complete:
            self.__objectives_result = True
        else:

            if self.__objectivesTimedOut() or any(
                    tuple(objective.failed()
                          for objective in self.__scenario_objectives)):

                self.__objectives_result = False
            else:
                self.__objectives_result = None

    def __dynamicGraphicItemsUpdate(self) -> None:

        if self.__condition_graphic_items:
            timestamp = time.time()
            if self.__start_scenario_time is not None:
                timestamp -= self.__start_scenario_time
            for dyn_gitem in self.__condition_graphic_items:
                dyn_gitem.evaluate(timestamp=timestamp)

    def __timerTimeout(self) -> None:

        if self.__current_scenario is None:
            return

        if self.__center_view_on is not None:
            self.__ui.view.centerOn(self.__center_view_on)

        ships = tuple(ship.device for ship in self.__ships)
        with self.__lock:
            self.__space.step(0.02)
            for ship_info in self.__ships:
                ship = ship_info.device
                ship.act()
                self.__updateGraphicsItem(ship.body, ship_info.gitem)

            for obj_body, gitem in self.__objects:
                self.__updateGraphicsItem(obj_body, gitem)

            if self.__comm_engine is not None:
                self.__comm_engine.step()

            self.__checkObjectives(ships)
            self.__dynamicGraphicItemsUpdate()

        if self.__objectives_result is not None:
            if self.__one_shot is True:
                self.__saveStatistics()
                self.close()
                return
            if self.__ui.actionSimulationAutoRestart.isChecked():
                self.__saveStatistics()
                self.loadScenario(self.__current_scenario)
                return

        for node_value in self.__objectives_node_value:
            node_value.update()

        self.__ui.view.scene().setBackgroundRect(
            self.__ui.view.mapToScene(self.__ui.view.rect()).boundingRect())

        self.__handleDebugMessages()

        self.__updateTitle()

    @staticmethod
    def __importAction(message: str, fileoptions: str,
                       filedatatype: 'FileInfo.FileDataType') -> None:

        fdialog = QFileDialog(None, message, '', fileoptions)
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addFiles(filedatatype, fdialog.selectedFiles())

    @staticmethod
    def __importScenarioAction() -> None:
        MainWindow.__importAction('Scenario Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.SCENARIO)

    @staticmethod
    def __importShipAction() -> None:
        MainWindow.__importAction('Ship Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.SHIPMODEL)

    @staticmethod
    def __importControllerAction() -> None:
        MainWindow.__importAction('Controller Import Dialog',
                                  'executable files(*)',
                                  FileInfo.FileDataType.CONTROLLER)

    @staticmethod
    def __importImageAction() -> None:
        MainWindow.__importAction('Image Import Dialog',
                                  'image files(*.png *.gif)',
                                  FileInfo.FileDataType.IMAGE)

    @staticmethod
    def __importObjectAction() -> None:
        MainWindow.__importAction('Object Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.OBJECTMODEL)

    @staticmethod
    def __importPackageAction() -> None:

        fdialog = QFileDialog(None, 'Controller Import Dialog')

        fdialog.setFileMode(QFileDialog.DirectoryOnly)

        if not fdialog.exec_():
            return

        for package in fdialog.selectedFiles():
            FileInfo().addPackage(package)

    def __deviceInterfaceComboBoxIndexChange(self, cur_index: int) -> None:

        if cur_index == -1 or cur_index >= len(self.__ships):
            return

        for widget in self.__ships[self.__current_ship_widgets_index].widgets:
            widget.hide()

        for widget in self.__ships[cur_index].widgets:
            widget.show()

        self.__current_ship_widgets_index = cur_index

    @staticmethod
    def __openAction(text: str, filedatatype: 'FileInfo.FileDataType') -> None:

        tree = FileInfo().listFilesTree(filedatatype, show_meta_files=True,
                                        show_hidden_files=True)

        if tree is None:
            return

        filepath = MainWindow.__getOptionDialog(text, tree.children)

        if filepath is not None:
            FileInfo().openFile(filedatatype, '/'.join(filepath))

    @staticmethod
    def __openScenarioAction() -> None:
        MainWindow.__openAction('Choose scenario',
                                FileInfo.FileDataType.SCENARIO)

    @staticmethod
    def __openShipAction() -> None:
        MainWindow.__openAction('Choose ship model',
                                FileInfo.FileDataType.SHIPMODEL)

    @staticmethod
    def __openControllerAction() -> None:
        MainWindow.__openAction('Choose controller',
                                FileInfo.FileDataType.CONTROLLER)

    @staticmethod
    def __openImageAction() -> None:
        MainWindow.__openAction('Choose image',
                                FileInfo.FileDataType.IMAGE)

    @staticmethod
    def __openObjectAction() -> None:
        MainWindow.__openAction('Choose object model',
                                FileInfo.FileDataType.OBJECTMODEL)

    @staticmethod
    def __autoRestartOptionToggled(checked: bool) -> None:
        fileinfo = FileInfo()
        fileinfo.writeConfig(checked, 'Simulation', 'auto_restart')
        fileinfo.saveConfig()

    @staticmethod
    def __fitAllOnStartToggled(checked: bool) -> None:
        fileinfo = FileInfo()
        fileinfo.writeConfig(checked, 'Simulation', 'fit_all_on_start')
        fileinfo.saveConfig()

    def __initConnections(self) -> None:

        self.__ui.actionLoadScenario.triggered.connect(
            self.__loadScenarioAction)

        self.__ui.actionImportScenario.triggered.connect(
            self.__importScenarioAction)

        self.__ui.actionImportShip.triggered.connect(
            self.__importShipAction)

        self.__ui.actionImportController.triggered.connect(
            self.__importControllerAction)

        self.__ui.actionImportImage.triggered.connect(
            self.__importImageAction)

        self.__ui.actionImportObject.triggered.connect(
            self.__importObjectAction)

        self.__ui.actionOpenScenario.triggered.connect(
            self.__openScenarioAction)

        self.__ui.actionOpenShip.triggered.connect(
            self.__openShipAction)

        self.__ui.actionOpenController.triggered.connect(
            self.__openControllerAction)

        self.__ui.actionOpenImage.triggered.connect(
            self.__openImageAction)

        self.__ui.actionOpenObject.triggered.connect(
            self.__openObjectAction)

        self.__ui.actionImportPackage.triggered.connect(
            self.__importPackageAction)

        self.__ui.deviceInterfaceComboBox.currentIndexChanged.connect(
            self.__deviceInterfaceComboBoxIndexChange)

        self.__ui.actionSimulationAutoRestart.toggled.connect(
            self.__autoRestartOptionToggled)

        self.__ui.actionFitAllOnStart.toggled.connect(
            self.__fitAllOnStartToggled)

        self.__ui.actionHelpHandbook.triggered.connect(
            self.__showHelp)

    def keyPressEvent(self, event: 'QKeyEvent') -> None:

        key = event.key()
        modifiers = event.modifiers()

        updated_view = False
        if modifiers == Qt.ControlModifier:
            if key == Qt.Key_Equal:
                self.__ui.view.scale(1.25, 1.25)
                updated_view = True
            elif key == Qt.Key_Minus:
                self.__ui.view.scale(1/1.25, 1/1.25)
                updated_view = True
            elif key == Qt.Key_A:
                self.__ui.view.rotate(-5)
                updated_view = True
            elif key == Qt.Key_D:
                self.__ui.view.rotate(5)
                updated_view = True
            elif key == Qt.Key_R:
                self.__ui.view.fitInView(
                    self.__ui.view.scene().itemsBoundingRect(),
                    Qt.KeepAspectRatio)
                updated_view = True
        else:
            if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                self.__ui.view.keyPressEvent(event)
                self.__ui.view.scale(2, 1)
                self.__ui.view.scale(.5, 1)
                updated_view = True

        if updated_view is True:
            self.__ui.view.scene().setBackgroundRect(
                self.__ui.view.mapToScene(self.__ui.view.rect()).boundingRect())
            self.__ui.view.repaint()
            return

        if Qt.Key_0 <= key <= Qt.Key_9:

            value = 9 if key == Qt.Key_0 else key - Qt.Key_1
            try:
                ship_item = self.__ships[value].gitem
            except IndexError:
                pass
            else:
                self.__ui.view.centerOn(ship_item.pos())
                if modifiers == Qt.ControlModifier:
                    self.__center_view_on = ship_item

    @staticmethod
    def __showHelp() -> None:
        HelpDialog().exec_()
