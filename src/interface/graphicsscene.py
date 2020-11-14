
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QRectF

class GraphicsScene(QGraphicsScene):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__image = None

    def setImage(self, image):
        self.__image = image

    def image(self):
        return self.__image

    def drawBackground(self, painter, rect) -> None:
        if self.__image is not None:

            bg_rect = QRectF(-1000, -1000, 2000, 2000)
            image_size = self.__image.size()

            source_rect = QRectF()

            source_rect.setX(image_size.width()*(rect.x() - bg_rect.x())/
                             bg_rect.width())
            source_rect.setY(image_size.height()*(rect.y() - bg_rect.y())/
                             bg_rect.height())
            source_rect.setWidth(rect.width()*image_size.width()/
                                 bg_rect.width())
            source_rect.setHeight(rect.height()*image_size.height()/
                                  bg_rect.height())

            print(source_rect, image_size, bg_rect)

            painter.drawImage(rect, self.__image, source_rect)
