
import html

from PyQt5.QtGui import QFontMetricsF
from PyQt5.QtWidgets import QLabel, QTextEdit
from PyQt5.QtCore import Qt

from .device import DefaultDevice

from ..utils.actionqueue import ActionQueue, Action

class InterfaceDevice(DefaultDevice):

    def __init__(self, **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__queue = ActionQueue()

    def act(self) -> None:
        self.__queue.processItems()

    def addAction(self, action: 'Action') -> None:
        self.__queue.add(action)

class TextDisplayDevice(InterfaceDevice):

    def __init__(self, **kwargs: 'Any') -> None:
        super().__init__(device_type='text-display', **kwargs)

        self.__label = QLabel('-')

        self.__label.setStyleSheet('''

            background-color: white;
            border-color: black;
            border-width: 1px;
            border-style: solid;
            font-family: "Courier";

        ''')

    @property
    def widget(self):
        return self.__label

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, TextDisplayDevice.__COMMANDS, *args)

    def setText(self, text: str) -> None:
        self.addAction(Action(QLabel.setText, self.__label, text))

    __COMMANDS = {

        'set-text': setText
    }

class ButtonDevice(InterfaceDevice):

    def __init__(self, button: 'PanelPushButton', **kwargs: 'Any') -> None:
        super().__init__(device_type='button', **kwargs)

        self.__button = button

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, ButtonDevice.__COMMANDS, *args)

    def __clicked(self) -> None:
        return '1' if self.__button.getPressed() else '0'

    __COMMANDS = {

        'clicked': __clicked
    }

class KeyboardReceiverDevice(InterfaceDevice):

    def __init__(self, kb_receiver: 'KeyboardButton', **kwargs: 'Any') -> None:
        super().__init__(device_type='keyboard', **kwargs)

        self.__receiver = kb_receiver

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command,
                               KeyboardReceiverDevice.__COMMANDS, *args)

    def __get(self) -> None:
        return self.__receiver.getAll()

    __COMMANDS = {

        'get': __get
    }

class ConsoleDevice(InterfaceDevice):

    def __init__(self, text: 'QTextEdit', columns: int, rows: int,
                 **kwargs: 'Any') -> None:
        super().__init__(device_type='console-text-display', **kwargs)

        self.__text_widget = text
        self.__col = 0
        self.__row = 0
        self.__total_cols = columns
        self.__total_rows = rows
        self.__text = ' '*(self.__total_cols*self.__total_rows)

        text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text.setFocusPolicy(Qt.NoFocus)

        tdoc = text.document()
        fmetrics = QFontMetricsF(tdoc.defaultFont())
        margins = text.contentsMargins()

        height = fmetrics.lineSpacing()*rows + \
            2*(tdoc.documentMargin() + text.frameWidth()) + \
                margins.top() + margins.bottom()


        width = fmetrics.width('A')*columns + \
            2*(tdoc.documentMargin() + text.frameWidth()) + \
                margins.left() + margins.right()

        text.setFixedHeight(height)
        text.setFixedWidth(width)

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, ConsoleDevice.__COMMANDS, *args)

    def __setPos(self, column_s, row_s):

        column = int(column_s)
        row = int(row_s)

        if column < 0 or column > self.__total_cols:
            return '<<err>>'

        if row < 0 or row > self.__total_rows:
            return '<<err>>'

        self.__col = column
        self.__row = row

        return '<<ok>>'

    def __getPos(self):
        return f'{self.__col}-{self.__row}'

    def __newline(self):

        if self.__row >= self.__total_rows:
            return '<<err>>'

        self.__row += 1
        self.__col = 0

        return '<<ok>>'

    def __columndec(self):
        if self.__col == 0:
            return '<<err>>'

        self.__col -= 1

        return '<<ok>>'

    def __columnstart(self):
        self.__col = 0

        return '<<ok>>'

    def __write(self, text):
        pos = self.__row*self.__total_cols + self.__col
        self.__text = self.__text[: pos] + text + self.__text[pos + len(text):]

        total_size = self.__total_cols*self.__total_rows
        if len(text) > total_size:
            self.__text = self.__text[: total_size]

        pos += len(text)
        self.__row = pos//self.__total_cols
        self.__col = pos%self.__total_cols

        return '<<ok>>'

    def __update(self):

        text = html.escape(self.__text).replace(' ', '&nbsp;')
        self.addAction(Action(QTextEdit.setHtml, self.__text_widget, text))

        return '<<ok>>'

    def __clear(self):
        self.__text = ' '*(self.__total_cols*self.__total_rows)

        return '<<ok>>'

    __COMMANDS = {

        'write': __write,
        'set-cursor-pos': __setPos,
        'get-cursor-pos': __getPos,
        'LF': __newline,
        'BS': __columndec,
        'CR': __columnstart,
        'update': __update,
        'clear': __clear
    }
