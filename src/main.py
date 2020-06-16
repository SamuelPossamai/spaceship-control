
import sys
import argparse
from collections import namedtuple

from PyQt5.QtWidgets import QApplication

from .interface.mainwindow import MainWindow
from .storage.fileinfo import FileInfo

ProgramArgsInfo = namedtuple('ProgramArgsInfo', (
    'scenario', 'one_shot', 'time_limit'))

def getProgramArguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Scenario that will be loaded')
    parser.add_argument('--one-shot', action='store_true', help=(
        'If specified, the program will be closed when the scenario finishs'))
    parser.add_argument('-f', '--file-path', help=(
        'Path to the file where information about the results of the last run '
        'will be stored'))
    parser.add_argument('-t', '--time-limit', type=float, help=(
        'If specified, the objectives will fail after \'n\' seconds'))

    args = parser.parse_args()

    if args.one_shot and args.scenario is None:
        print('\'--one-shot\' can only be used together with \'--scenario\'',
              file=sys.stderr)
        sys.exit(-1)

    if args.file_path is not None:
        FileInfo().statistics_filepath = args.file_path

    return ProgramArgsInfo(scenario=args.scenario, one_shot=args.one_shot,
                           time_limit=args.time_limit)

def main():

    program_args = getProgramArguments()

    app = QApplication(sys.argv)

    window = MainWindow(one_shot=program_args.one_shot,
                        time_limit=program_args.time_limit)
    window.show()

    if program_args.scenario is not None:
        window.loadScenario(program_args.scenario)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
