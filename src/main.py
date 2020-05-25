
import sys
import argparse
from collections import namedtuple

from PyQt5.QtWidgets import QApplication

from .interface.mainwindow import MainWindow

ProgramArgsInfo = namedtuple('ProgramArgsInfo', ('scenario',))

def getProgramArguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Scenario that will be loaded')

    args = parser.parse_args()

    return ProgramArgsInfo(scenario=args.scenario)

def main():

    program_args = getProgramArguments()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    if program_args.scenario is not None:
        window.loadScenario(program_args.scenario)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
