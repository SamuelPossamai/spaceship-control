
import sys
import argparse
from collections import namedtuple

from PyQt5.QtWidgets import QApplication

from .interface.mainwindow import MainWindow
from .storage.fileinfo import FileInfo

ProgramArgsInfo = namedtuple('ProgramArgsInfo', (
    'scenario', 'one_shot', 'time_limit', 'follow_ship', 'start_zoom',
    'timer_interval'))

def getProgramArguments() -> 'ProgramArgsInfo':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Scenario that will be loaded')
    parser.add_argument('--one-shot', action='store_true', help=(
        'If specified, the program will be closed when the scenario finishs'))
    parser.add_argument('-f', '--file-path', help=(
        'Path to the file where information about the results of the last run '
        'will be stored'))
    parser.add_argument('-t', '--time-limit', type=float, help=(
        'If specified, the objectives will fail after \'n\' seconds'))
    parser.add_argument('--follow', type=int, help=(
        'Start following the ship number \'n\''))
    parser.add_argument('--zoom', type=float, help='Starting zoom')
    parser.add_argument('--timer-interval', type=int, default=100, help=(
        'Time in milliseconds between each simulation \'step\''))

    args = parser.parse_args()

    if args.one_shot and args.scenario is None:
        print('\'--one-shot\' can only be used together with \'--scenario\'',
              file=sys.stderr)
        sys.exit(-1)

    if args.file_path is not None:
        FileInfo().statistics_filepath = args.file_path

    return ProgramArgsInfo(scenario=args.scenario,
                           one_shot=args.one_shot,
                           time_limit=args.time_limit,
                           follow_ship=args.follow,
                           start_zoom=args.zoom,
                           timer_interval=args.timer_interval)

def main() -> None:

    program_args = getProgramArguments()

    app = QApplication(sys.argv)

    window = MainWindow(one_shot=program_args.one_shot,
                        time_limit=program_args.time_limit,
                        follow_ship=program_args.follow_ship,
                        start_zoom=program_args.start_zoom,
                        timer_interval=program_args.timer_interval)
    window.show()

    if program_args.scenario is not None:
        window.loadScenario(program_args.scenario)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
