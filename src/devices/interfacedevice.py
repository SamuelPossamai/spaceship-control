
import html
from typing import TYPE_CHECKING

from PyQt5.QtGui import QFontMetricsF, QFont
from PyQt5.QtWidgets import QLabel, QTextEdit
from PyQt5.QtCore import Qt

from .device import DefaultDevice

from ..utils.actionqueue import ActionQueue, Action

from ..interface.panelpushbutton import PanelPushButton
from ..interface.keyboardbutton import KeyboardButton

if TYPE_CHECKING:
    from typing import Any, List, Callable, Dict
    from PyQt5.QtWidgets import QWidget

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
    def widget(self) -> 'QWidget':
        return self.__label

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable[..., Any]]') -> 'Any':
        return super().command(command, TextDisplayDevice.__COMMANDS, *args)

    def setText(self, text: str) -> None:
        self.addAction(Action(QLabel.setText, self.__label, text))

    __COMMANDS = {

        'set-text': setText
    }

class ButtonDevice(InterfaceDevice):

    def __init__(self, **kwargs: 'Any') -> None:
        super().__init__(device_type='button', **kwargs)

        self.__button = PanelPushButton()

        self.__button.setFocusPolicy(Qt.NoFocus)

        self.__button.setStyleSheet('background-color: red;')

    @property
    def widget(self) -> 'QWidget':
        return self.__button

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable[..., Any]]') -> 'Any':
        return super().command(command, ButtonDevice.__COMMANDS, *args)

    def __clicked(self) -> str:
        return '1' if self.__button.getPressed() else '0'

    __COMMANDS = {

        'clicked': __clicked
    }

class KeyboardReceiverDevice(InterfaceDevice):

    def __init__(self, **kwargs: 'Any') -> None:
        super().__init__(device_type='keyboard', **kwargs)

        self.__receiver = KeyboardButton()

    @property
    def widget(self) -> 'QWidget':
        return self.__receiver

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable[..., Any]]') -> 'Any':
        return super().command(command,
                               KeyboardReceiverDevice.__COMMANDS, *args)

    def __get(self) -> 'Any':
        return self.__receiver.getAll()

    def __activate(self) -> str:
        self.__receiver.setFocus()
        return '<<OK>>'

    def __desactivate(self) -> str:
        self.__receiver.clearFocus()
        return '<<OK>>'

    __COMMANDS = {
        'get': __get,
        'activate': __activate,
        'desactivate': __desactivate
    }

class ConsoleDevice(InterfaceDevice):

    def __init__(self, columns: int, rows: int, **kwargs: 'Any') -> None:
        super().__init__(device_type='console-text-display', **kwargs)

        self.__text_widget = text = QTextEdit()
        self.__col = 0
        self.__row = 0
        self.__total_cols = columns
        self.__total_rows = rows
        self.__text = ' '*(self.__total_cols*self.__total_rows)

        text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text.setFocusPolicy(Qt.NoFocus)

        text.setReadOnly(True)

        text.setStyleSheet('''

            color: white;
            background-color: black;
            border-color: black;
            border-width: 1px;
            border-style: solid;
        ''')

        font = QFont('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        text.setFont(font)

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

    @property
    def widget(self) -> 'QWidget':
        return self.__text_widget

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, ConsoleDevice.__COMMANDS, *args)

    def __setPosX(self, column_s: str) -> str:

        column = int(column_s)

        if column < 0 or column > self.__total_cols:
            return '<<err>>'

        self.__col = column

        return '<<ok>>'

    def __setPosY(self, row_s: str) -> str:

        row = int(row_s)

        if row < 0 or row > self.__total_rows:
            return '<<err>>'

        self.__row = row

        return '<<ok>>'

    def __setPos(self, column_s: str, row_s: str) -> str:

        column = int(column_s)
        row = int(row_s)

        if column < 0 or column > self.__total_cols:
            return '<<err>>'

        if row < 0 or row > self.__total_rows:
            return '<<err>>'

        self.__col = column
        self.__row = row

        return '<<ok>>'

    def __getPosX(self) -> int:
        return self.__col

    def __getPosY(self) -> int:
        return self.__row

    def __getPos(self) -> str:
        return f'{self.__col}-{self.__row}'

    def __newline(self) -> str:

        if self.__row >= self.__total_rows:
            return '<<err>>'

        self.__row += 1
        self.__col = 0

        return '<<ok>>'

    def __columndec(self) -> str:
        if self.__col == 0:
            return '<<err>>'

        self.__col -= 1

        return '<<ok>>'

    def __columnstart(self) -> str:
        self.__col = 0

        return '<<ok>>'

    def __write(self, text: str) -> str:
        pos = self.__row*self.__total_cols + self.__col
        self.__text = self.__text[: pos] + text + self.__text[pos + len(text):]

        total_size = self.__total_cols*self.__total_rows
        if len(self.__text) > total_size:
            self.__text = self.__text[: total_size]

        pos += len(text)
        self.__row = pos//self.__total_cols
        self.__col = pos%self.__total_cols

        return '<<ok>>'

    def __update(self) -> str:

        pos = self.__row*self.__total_cols + self.__col

        i = 0
        for i, char in enumerate(reversed(self.__text)):
            if char != ' ':
                break

        last_space = len(self.__text) - i
        if last_space <= pos:
            last_space = pos + 1

        pos_text = self.__text[pos]
        text_before = html.escape(self.__text[:pos]).replace(' ', '&nbsp;')
        text_after = html.escape(self.__text[pos+1:last_space+1]).replace(
            ' ', '&nbsp;')

        text = (
            f'{text_before}<font color="black" style="background-color: '
            f'white;">{pos_text}</font>{text_after}')

        self.addAction(Action(QTextEdit.setHtml, self.__text_widget, text))

        return '<<ok>>'

    def __clear(self) -> str:
        self.__text = ' '*(self.__total_cols*self.__total_rows)

        return '<<ok>>'

    __COMMANDS: 'Dict[str, Callable[..., Any]]' = {

        'write': __write,
        'set-cursor-pos-x': __setPosX,
        'set-cursor-pos-y': __setPosY,
        'set-cursor-pos': __setPos,
        'get-cursor-pos-x': __getPosX,
        'get-cursor-pos-y': __getPosY,
        'get-cursor-pos': __getPos,
        'LF': __newline,
        'BS': __columndec,
        'CR': __columnstart,
        'update': __update,
        'clear': __clear
    }
