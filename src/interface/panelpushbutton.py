
from PyQt5.QtWidgets import QPushButton

class PanelPushButton(QPushButton):

    def __init__(self) -> None:
        super().__init__()

        self.__was_pressed = False
        self.clicked.connect(self.setPressed)

    def setPressed(self) -> None:
        self.__was_pressed = True

    def getPressed(self, reset: bool = True) -> bool:
        pressed = self.__was_pressed
        if pressed and reset:
            self.__was_pressed = False

        return pressed
