
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QRectF

class GraphicsScene(QGraphicsScene):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__bg_image = None
        self.__bg_rect = None
        self.__fg_image = None
        self.__fg_rect = None

    def setBackgroundImage(self, image):
        self.__bg_image = image

    def backgroundImage(self):
        return self.__bg_image

    def setForegroundImage(self, image):
        self.__fg_image = image

    def foregroundImage(self):
        return self.__fg_image

    def setBackgroundRect(self, rect):
        self.__bg_rect = rect

    def backgroundRect(self):
        return self.__bg_rect

    def setForegroundRect(self, rect):
        self.__fg_rect = rect

    def foregroundRect(self):
        return self.__fg_rect

    def __draw(self, painter, rect, image, bg_rect):

        if image is not None and bg_rect is not None:

            image_size = image.size()

            source_rect = QRectF()
            try:
                source_rect.setX(image_size.width()*(rect.x() - bg_rect.x())/
                                 bg_rect.width())
                source_rect.setY(image_size.height()*(rect.y() - bg_rect.y())/
                                 bg_rect.height())
                source_rect.setWidth(rect.width()*image_size.width()/
                                     bg_rect.width())
                source_rect.setHeight(rect.height()*image_size.height()/
                                      bg_rect.height())
            except ZeroDivisionError:
                pass
            else:
                painter.drawImage(rect, image, source_rect)

    def drawBackground(self, painter, rect) -> None:
        self.__draw(painter, rect, self.__bg_image, self.__bg_rect)

    def drawForeground(self, painter, rect) -> None:
        self.__draw(painter, rect, self.__fg_image, self.__fg_rect)
