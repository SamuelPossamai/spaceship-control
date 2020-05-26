
import sys
import argparse
from collections import namedtuple

from PyQt5.QtWidgets import QApplication

from .interface.mainwindow import MainWindow

ProgramArgsInfo = namedtuple('ProgramArgsInfo', ('scenario', 'one_shot'))

def getProgramArguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Scenario that will be loaded')
    parser.add_argument('--one-shot', action='store_true', help=(
        'If specified, the program will be closed when the scenario finishs'))

    args = parser.parse_args()

    if args.one_shot and args.scenario is None:
        print('\'--one-shot\' can only be used together with \'--scenario\'',
              file=sys.stderr)
        sys.exit(-1)

    return ProgramArgsInfo(scenario=args.scenario, one_shot=args.one_shot)

def main():

    program_args = getProgramArguments()

    app = QApplication(sys.argv)

    window = MainWindow(one_shot=program_args.one_shot)
    window.show()

    if program_args.scenario is not None:
        window.loadScenario(program_args.scenario)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
