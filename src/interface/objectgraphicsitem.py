
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPolygonF

import pymunk

class DrawingPart(ABC):

    def paint(self, painter, option, widget) -> None:
        painter.save()
        self._paint(painter, option, widget)
        painter.restore()

    @abstractmethod
    def boundingRect(self) -> QRectF:
        pass

    @abstractmethod
    def _paint(self, painter, option, widget) -> None:
        pass

class EllipseDrawingPart(DrawingPart):

    def __init__(self, height, width, color=None,
                 border_color=None, brush_color=None,
                 offset=QPointF(0, 0)):
        super().__init__()

        if border_color is None:
            self.__b_color = color
        else:
            self.__b_color = border_color

        if brush_color is None:
            self.__color = color
        else:
            self.__color = brush_color
        self.__offset = offset
        self.__a_radius = height/2
        self.__b_radius = width/2

    def boundingRect(self) -> QRectF:
        return QRectF(-self.__b_radius, -self.__a_radius, 2*self.__a_radius,
                      2*self.__b_radius)

    def _paint(self, painter, option, widget) -> None:
        if self.__b_color is not None:
            pen = painter.pen()
            pen.setColor(self.__b_color)
            painter.setPen(pen)
        if self.__color is not None:
            painter.setBrush(self.__color)

        painter.drawEllipse(self.__offset, self.__b_radius, self.__a_radius)

class CircleDrawingPart(EllipseDrawingPart):

    def __init__(self, radius, **kwargs) -> None:
        super().__init__(2*radius, 2*radius, **kwargs)

class LineDrawingPart(DrawingPart):

    def __init__(self, start, end, color=None, width=None) -> None:
        super().__init__()

        self.__start = start
        self.__end = end
        self.__color = color
        self.__width = width

    def boundingRect(self) -> QRectF:
        start_x = self.__start.x()
        start_y = self.__start.y()
        end_x = self.__end.x()
        end_y = self.__end.y()
        return QRectF(start_x, start_y, end_x - start_x, end_y - start_y)

    def _paint(self, painter, option, widget) -> None:
        if self.__color is not None or self.__width is not None:
            pen = painter.pen()
            if self.__color is not None:
                pen.setColor(self.__color)
            if self.__width is not None:
                pen.setWidthF(self.__width)
            painter.setPen(pen)

        painter.drawLine(self.__start, self.__end)

class PolyDrawingPart(DrawingPart):

    def __init__(self, points, color=None, border_color=None,
                 brush_color=None) -> None:
        super().__init__()

        if border_color is None:
            self.__b_color = color
        else:
            self.__b_color = border_color

        if brush_color is None:
            self.__color = color
        else:
            self.__color = brush_color

        self.__points = tuple(points)

        self.__polygon = QPolygonF()
        for point in points:
            self.__polygon.append(point)

    def boundingRect(self) -> QRectF:
        x_val_key = lambda point: point.x()
        y_val_key = lambda point: point.y()
        min_x = min(self.__points, key=x_val_key).x()
        min_y = min(self.__points, key=y_val_key).y()
        max_x = max(self.__points, key=x_val_key).x()
        max_y = max(self.__points, key=y_val_key).y()
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def _paint(self, painter, option, widget) -> None:
        if self.__b_color is not None:
            pen = painter.pen()
            pen.setColor(self.__b_color)
            painter.setPen(pen)
        if self.__color is not None:
            painter.setBrush(self.__color)

        painter.drawPolygon(self.__polygon)

class ObjectGraphicsItem(QGraphicsItem):

    def __init__(self, shapes, color=Qt.blue) -> None:
        super().__init__()

        self.__parts = []
        for shape in shapes:
            if isinstance(shape, pymunk.Circle):
                offset_pym = shape.offset
                offset = QPointF(offset_pym.x, offset_pym.y)
                circle = CircleDrawingPart(shape.radius, color=color,
                                           offset=offset)
                self.__parts.append(circle)

            elif isinstance(shape, pymunk.Poly):
                points = tuple(QPointF(point.x, point.y) for point in
                               shape.get_vertices())
                self.__parts.append(PolyDrawingPart(points, color=color))

            elif isinstance(shape, pymunk.Segment):
                self.__parts.append(LineDrawingPart(
                    QPointF(shape.a.x, shape.a.y),
                    QPointF(shape.b.x, shape.a.y),
                    color=color, width=shape.radius))

        self.__bounding_rect = QRectF(0, 0, 0, 0)
        for part in self.__parts:
            self.__bounding_rect |= part.boundingRect()

    @staticmethod
    def boundingRect() -> QRectF:
        return QRectF(-100, -100, 200, 200)

    def paint(self, painter, option, widget) -> None:

        for part in self.__parts:
            part.paint(painter, option, widget)
