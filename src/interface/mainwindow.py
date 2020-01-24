
import signal
from math import pi
from threading import Thread, Lock
from subprocess import Popen, PIPE

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog
from PyQt5.QtCore import QTimer

import pymunk

from .shipgraphicsitem import ShipGraphicsItem
from .choosefromtreedialog import ChooseFromTreeDialog

from ..utils.fileinfo import FileInfo
from ..utils.shiploader import loadShip
from ..utils import scenarioloader
from ..utils.actionqueue import ActionQueue

UiMainWindow, _ = uic.loadUiType(FileInfo().uiFilePath('mainwindow.ui'))

class MainWindow(QMainWindow):

    def __init__(self, parent=None):

        QMainWindow.__init__(self, parent=parent)

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
        self.__action_queue = ActionQueue()

        self.__ships = []

        self.__ui.actionLoadScenario.triggered.connect(
            self.__loadScenarioAction)

        self.__ui.actionImportScenario.triggered.connect(
            self.__importScenarioAction)

        self.__ui.actionImportShip.triggered.connect(
            self.__importShipAction)

        self.__ui.actionImportController.triggered.connect(
            self.__importControllerAction)

    def clear(self):

        with self.__lock:
            self.__space.remove(self.__space.bodies, self.__space.shapes)
            for ship, gitem, widgets, _ in self.__ships:
                self.__ui.view.scene().removeItem(gitem)
                for widget in widgets:
                    widget.setParent(None)

            self.__ships = []

    def __loadScenarioAction(self):

        dialog = ChooseFromTreeDialog(FileInfo().listScenariosTree().children)
        dialog.setWindowTitle('Choose scenario')

        scenario = dialog.getOption()
        if scenario is not None:
            self.loadScenario('/'.join(scenario))

    def loadScenario(self, scenario):

        self.clear()

        fileinfo = FileInfo()

        scenario_path = fileinfo.scenarioPath(scenario + '.toml')
        scenario_info = scenarioloader.loadScenario(scenario_path)

        self.__ships = [None]*len(scenario_info.ships)
        for i, ship_info in enumerate(scenario_info.ships):

            ship, widgets, shapes = loadShip(
                fileinfo.shipModelPath(ship_info.model + '.toml'), self.__space,
                self.__action_queue)

            self.__widgets = widgets
            ship.body.position = ship_info.position
            ship.body.angle = ship_info.angle

            for widget in widgets:
                widget.setParent(self.__ui.deviceInterfaceComponents)

            controller_path = fileinfo.controllerPath(ship_info.controller)
            thread = Thread(target=self.__startController, daemon=True,
                            args=([controller_path], ship, self.__lock))

            ship_gitem = ShipGraphicsItem(shapes)
            self.__ui.view.scene().addItem(ship_gitem)
            self.__ships[i] = (ship, ship_gitem, widgets, thread)

            thread.start()

        for widget in self.__ships[0][2]:
            widget.show()

    def __timerTimeout(self):

        self.__action_queue.processItems()

        with self.__lock:
            self.__space.step(0.02)
            for ship, gitem, _, _ in self.__ships:
                ship.act()
                pos = ship.body.position
                gitem.setX(pos.x/10)
                gitem.setY(pos.y/10)
                gitem.prepareGeometryChange()
                gitem.setRotation(180*ship.body.angle/pi)

    def __startController(self, program, device, lock):

        process = Popen(program, stdin=PIPE,
                        stdout=PIPE)

        try:
            while process.poll() is None:
                question = process.stdout.readline().decode()

                if question and question[-1] == '\n':
                    question = question[:-1]

                with lock:
                    if device.isDestroyed():
                        break
                    answer = device.communicate(question)

                process.stdin.write(answer.encode())
                process.stdin.write(b'\n')
                process.stdin.flush()

        except BrokenPipeError:
            pass

        process.send_signal(signal.SIGHUP)

    def __importScenarioAction(self):

        fdialog = QFileDialog(None, 'Scenario Import Dialog', '',
                              'TOML files(*.toml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addScenarios(fdialog.selectedFiles())

    def __importShipAction(self):

        fdialog = QFileDialog(None, 'Ship Import Dialog', '',
                              'TOML files(*.toml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addShips(fdialog.selectedFiles())

    def __importControllerAction(self):
        pass
