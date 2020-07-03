
import sys
import time
from math import pi
from threading import Lock
from pathlib import Path
from queue import Empty as EmptyQueueException

from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QFileDialog, QMessageBox, QTextBrowser
)
from PyQt5.QtCore import QTimer, Qt

import pymunk

import anytree

# pylint: disable=relative-beyond-top-level

from .choosefromtreedialog import ChooseFromTreeDialog
from .loadgraphicitem import loadGraphicItem
from .loadship import loadShip

from ..storage.fileinfo import FileInfo

from ..objectives.objective import createObjectiveTree

# pylint: enable=relative-beyond-top-level

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))

# imported here so it is not imported in a different path

from nodetreeview import NodeValue # pylint: disable=wrong-import-order, wrong-import-position
UiMainWindow, _ = FileInfo().loadUi('mainwindow.ui') # pylint: disable=invalid-name
sys.path.pop(0)

class ObjectiveNodeValue(NodeValue):

    def __init__(self, objective):
        super().__init__(objective.name, objective.description)

        self.__objective = objective

    def update(self):
        if self.__objective.accomplished():
            symbol = '✓ '
        elif self.__objective.failed():
            symbol = '✗ '
        else:
            symbol = ''
        self.name = f'{symbol}{self.__objective.name}'

class MainWindow(QMainWindow):

    def __init__(self, parent=None, one_shot=False, time_limit=None,
                 follow_ship=None, start_zoom=None):

        super().__init__(parent=parent)

        self.__ui = UiMainWindow()
        self.__ui.setupUi(self)

        self.__ui.view.setScene(QGraphicsScene(parent))

        self.__lock = Lock()

        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__timerTimeout)

        self.__timer.setInterval(100)
        self.__timer.start()

        self.__space = pymunk.Space()
        self.__space.gravity = (0, 0)

        self.__ships = []
        self.__objects = []
        self.__scenario_objectives = []
        self.__objectives_result = None
        self.__current_scenario = None

        self.__widgets = []
        self.__objectives_node_value = []

        self.__title_basename = 'Spaceship Control'

        view_geometry = self.__ui.view.geometry()
        view_geometry.setWidth(self.geometry().width()//2)
        self.__ui.view.setGeometry(view_geometry)
        self.__updateTitle()

        self.__current_ship_widgets_index = 0

        self.__comm_engine = None
        self.__debug_msg_queues = {}

        self.__debug_messages_text_browsers = {}
        self.__condition_graphic_items = []

        self.__ship_to_follow = follow_ship

        self.__one_shot = one_shot
        self.__start_scenario_time = None
        self.__time_limit = time_limit

        self.__ui.actionSimulationAutoRestart.setChecked(
            FileInfo().readConfig('Simulation', 'auto_restart', default=False))

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

    def moveEvent(self, event): # pylint: disable=no-self-use
        FileInfo().writeConfig(event.pos().x(), 'Window', 'x')
        FileInfo().writeConfig(event.pos().y(), 'Window', 'y')
        FileInfo().saveConfig()

    def resizeEvent(self, event): # pylint: disable=no-self-use
        FileInfo().writeConfig(event.size().width(), 'Window', 'width')
        FileInfo().writeConfig(event.size().height(), 'Window', 'height')
        FileInfo().saveConfig()

    def __updateTitle(self):

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

    def closeEvent(self, _event):
        self.clear()
        self.__ui.view.setScene(None)

    def clear(self):

        self.setWindowTitle(self.__title_basename)

        self.__ui.deviceInterfaceComboBox.clear()
        self.__ui.deviceInterfaceComponents.show()
        self.__ui.treeView.show()

        self.__start_scenario_time = None
        self.__center_view_on = None

        with self.__lock:
            self.__space.remove(*self.__space.bodies, *self.__space.shapes)

            scene = self.__ui.view.scene()
            for _, _, widgets, _ in self.__ships:
                for widget in widgets:
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
    def __getOptionDialog(title, options):

        dialog = ChooseFromTreeDialog(options)
        dialog.setWindowTitle(title)

        return dialog.getOption()

    def __loadScenarioAction(self):

        scenario = self.__getOptionDialog(
            'Choose scenario', FileInfo().listFilesTree(
                FileInfo.FileDataType.SCENARIO).children)

        if scenario is not None:
            self.loadScenario('/'.join(scenario))

    def __chooseShipDialog(self, ship_options):
        return self.__getOptionDialog('Choose ship model', ship_options)

    def __chooseControllerDialog(self, controller_options):
        return self.__getOptionDialog('Choose controller', controller_options)

    def __loadShip(self, ship_info, arg_scenario_info):

        loaded_ship_info = loadShip(
            self.__space, ship_info, arg_scenario_info, self.__lock,
            ship_options_dialog=self.__chooseShipDialog,
            controller_options_dialog=self.__chooseControllerDialog,
            communication_engine=self.__comm_engine)

        ship = loaded_ship_info[0]
        ship_gitem = loaded_ship_info[1]
        thread = loaded_ship_info[3]

        self.__widgets = loaded_ship_info[2]

        for widget in self.__widgets:
            widget.setParent(self.__ui.deviceInterfaceComponents)

        self.__debug_msg_queues[ship.name] = loaded_ship_info[4]

        self.__condition_graphic_items.extend(loaded_ship_info[5])

        self.__ui.view.scene().addItem(ship_gitem)

        self.__ui.deviceInterfaceComboBox.addItem(
            f'{ship_info.name} ({ship_info.model})')

        thread.start()

        return ship, ship_gitem, self.__widgets, thread

    def __loadObject(self, obj_info, fileinfo):

        obj_model = obj_info.model
        if obj_model is None:
            options = fileinfo.listFilesTree(
                FileInfo.FileDataType.OBJECTMODEL).children
            obj_model = self.__getOptionDialog('Choose object model',
                                               options)

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

    def __loadScenarioShips(self, ships_info, arg_scenario_info):

        ships = [None]*len(ships_info)
        for i, ship_info in enumerate(ships_info):
            try:
                ship = self.__loadShip(ship_info, arg_scenario_info.copy())
            except Exception as err:
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading a ship({ship_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return None

            if ship is None:
                self.clear()
                return None

            ships[i] = ship

        if self.__ship_to_follow is not None:
            try:
                _, ship_item, _, _ = ships[self.__ship_to_follow]
            except IndexError:
                pass
            else:
                self.__ui.view.centerOn(ship_item.pos())
                self.__center_view_on = ship_item

        return ships

    def __loadScenarioObjects(self, objects_info):

        objects = [None]*len(objects_info)
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

        return objects

    def __loadStaticImages(self, static_images):

        if static_images:
            for image_info in static_images:
                image_item, condition_graphic_items = loadGraphicItem(
                    None, (image_info,), group_z_value=-1)

                self.__condition_graphic_items.extend(condition_graphic_items)

                self.__ui.view.scene().addItem(image_item)

    def loadScenario(self, scenario):

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

        space_info = scenario_info.physics_engine
        self.__space.damping = space_info.damping
        self.__space.gravity = space_info.gravity
        self.__space.collision_slop = space_info.collision_slop
        self.__space.collision_persistence = space_info.collision_persistence
        self.__space.iterations = space_info.iterations

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
            for widget in self.__ships[0][2]:
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

        self.__ui.debugMessagesTabWidget.clear()
        self.__debug_messages_text_browsers.clear()
        for ship, _, _, _ in ships:
            tbrowser = QTextBrowser()
            self.__debug_messages_text_browsers[ship.name] = tbrowser
            self.__ui.debugMessagesTabWidget.addTab(tbrowser, ship.name)

    @staticmethod
    def __updateGraphicsItem(body, gitem):

        pos = body.position
        gitem.setX(pos.x)
        gitem.setY(pos.y)
        gitem.prepareGeometryChange()
        gitem.setRotation(180*body.angle/pi)

    def __objectivesTimedOut(self):

        if self.__time_limit is None or self.__start_scenario_time is None:
            return False

        return time.time() - self.__start_scenario_time > self.__time_limit

    def __createObjectivesRecord(self, node, current_time):

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


    def __saveStatistics(self):

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

    def __timerTimeout(self):

        if self.__current_scenario is None:
            return

        if self.__center_view_on is not None:
            self.__ui.view.centerOn(self.__center_view_on)

        ships = tuple(ship for ship, _, _, _ in self.__ships)
        with self.__lock:
            self.__space.step(0.02)
            for ship, gitem, _, _ in self.__ships:
                ship.act()
                self.__updateGraphicsItem(ship.body, gitem)

            for obj_body, gitem in self.__objects:
                self.__updateGraphicsItem(obj_body, gitem)

            self.__comm_engine.step()

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

            if self.__condition_graphic_items:
                timestamp = time.time()
                if self.__start_scenario_time is not None:
                    timestamp -= self.__start_scenario_time
                for dyn_gitem in self.__condition_graphic_items:
                    dyn_gitem.evaluate(timestamp=timestamp)

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

        for ship_name, queue in self.__debug_msg_queues.items():
            tbrowser = self.__debug_messages_text_browsers.get(ship_name)
            if tbrowser is None:
                continue

            try:
                while not queue.empty():
                    tbrowser.append(queue.get_nowait())
            except EmptyQueueException:
                pass

        self.__updateTitle()

    @staticmethod
    def __importAction(message, fileoptions, filedatatype):

        fdialog = QFileDialog(None, message, '', fileoptions)
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addFiles(filedatatype, fdialog.selectedFiles())

    @staticmethod
    def __importScenarioAction():
        MainWindow.__importAction('Scenario Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.SCENARIO)

    @staticmethod
    def __importShipAction():
        MainWindow.__importAction('Ship Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.SHIPMODEL)

    @staticmethod
    def __importControllerAction():
        MainWindow.__importAction('Controller Import Dialog',
                                  'executable files(*)',
                                  FileInfo.FileDataType.CONTROLLER)

    @staticmethod
    def __importImageAction():
        MainWindow.__importAction('Image Import Dialog',
                                  'image files(*.png *.gif)',
                                  FileInfo.FileDataType.IMAGE)

    @staticmethod
    def __importObjectAction():
        MainWindow.__importAction('Object Import Dialog',
                                  'TOML files(*.toml) ;; JSON files(*.json) ;;'
                                  'YAML files(*.yml *.yaml)',
                                  FileInfo.FileDataType.OBJECTMODEL)

    @staticmethod
    def __importPackageAction():

        fdialog = QFileDialog(None, 'Controller Import Dialog')

        fdialog.setFileMode(QFileDialog.DirectoryOnly)

        if not fdialog.exec_():
            return

        for package in fdialog.selectedFiles():
            FileInfo().addPackage(package)

    def __deviceInterfaceComboBoxIndexChange(self, cur_index):

        if cur_index == -1 or cur_index >= len(self.__ships):
            return

        for widget in self.__ships[self.__current_ship_widgets_index][2]:
            widget.hide()

        for widget in self.__ships[cur_index][2]:
            widget.show()

        self.__current_ship_widgets_index = cur_index

    @staticmethod
    def __openAction(text, filedatatype):

        filepath = MainWindow.__getOptionDialog(
            text, FileInfo().listFilesTree(filedatatype).children)

        if filepath is not None:
            FileInfo().openFile(filedatatype, '/'.join(filepath))

    @staticmethod
    def __openScenarioAction():
        MainWindow.__openAction('Choose scenario',
                                FileInfo.FileDataType.SCENARIO)

    @staticmethod
    def __openShipAction():
        MainWindow.__openAction('Choose ship model',
                                FileInfo.FileDataType.SHIPMODEL)

    @staticmethod
    def __openControllerAction():
        MainWindow.__openAction('Choose controller',
                                FileInfo.FileDataType.CONTROLLER)

    @staticmethod
    def __openImageAction():
        MainWindow.__openAction('Choose image',
                                FileInfo.FileDataType.IMAGE)

    @staticmethod
    def __openObjectAction():
        MainWindow.__openAction('Choose object model',
                                FileInfo.FileDataType.OBJECTMODEL)

    @staticmethod
    def __autoRestartOptionToggled(checked):
        fileinfo = FileInfo()
        fileinfo.writeConfig(checked, 'Simulation', 'auto_restart')
        fileinfo.saveConfig()

    def __initConnections(self):

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

    def keyPressEvent(self, event):

        key = event.key()
        modifiers = event.modifiers()

        if modifiers == Qt.ControlModifier:
            if key == Qt.Key_Equal:
                self.__ui.view.scale(1.25, 1.25)
                return
            if key == Qt.Key_Minus:
                self.__ui.view.scale(1/1.25, 1/1.25)
                return
            if key == Qt.Key_A:
                self.__ui.view.rotate(-5)
                return
            if key == Qt.Key_D:
                self.__ui.view.rotate(5)
                return
            if key == Qt.Key_R:
                self.__ui.view.fitInView(
                    self.__ui.view.scene().itemsBoundingRect(),
                    Qt.KeepAspectRatio)
                return
        else:
            if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                self.__ui.view.keyPressEvent(event)
                return

        if Qt.Key_0 <= key <= Qt.Key_9:

            value = 9 if key == Qt.Key_0 else key - Qt.Key_1
            try:
                _, ship_item, _, _ = self.__ships[value]
            except IndexError:
                pass
            else:
                self.__ui.view.centerOn(ship_item.pos())
                if modifiers == Qt.ControlModifier:
                    self.__center_view_on = ship_item
