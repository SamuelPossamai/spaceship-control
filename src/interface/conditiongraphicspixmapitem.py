
from math import isclose
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QTransform

from ..utils.expression import Condition, Expression

if TYPE_CHECKING:
    from typing import Optional, Any, Dict
    from PyQt5.QtGui import QPixmap

class ConditionGraphicsPixmapItem(QGraphicsPixmapItem):

    def __init__(self, condition: 'Optional[str]', *args: 'Any',
                 names: 'Optional[Dict[str, Any]]' = None,
                 **kwargs: 'Any') -> None:
        super().__init__(*args, **kwargs)

        self.__condition = Condition(condition) if condition else None
        self.__is_visible = True
        self.__condition_met = False
        self.__names = {} if names is None else names.copy()
        self.__x_offset_func: 'Optional[Expression]' = None
        self.__y_offset_func: 'Optional[Expression]' = None
        self.__x_offset_func_mul: float = 1
        self.__y_offset_func_mul: float = 1
        self.__x_offset_calc: float = 0
        self.__y_offset_calc: float = 0
        self.__angle_offset_func: 'Optional[Expression]' = None
        self.__angle_offset_calc: float = 0

        self.__pixmap = super().pixmap()

        self.evaluate()

    def show(self) -> None:
        self.setVisible(True)

    def hide(self) -> None:
        self.setVisible(False)

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible and self.__condition_met)
        self.__is_visible = visible

    def isVisible(self) -> bool:
        return self.__is_visible

    def setPixmap(self, pixmap: 'QPixmap') -> None:
        super().setPixmap(pixmap)

        self.__pixmap = pixmap

    def setOffset(self, *args: 'Any') -> None:
        super().setOffset(*args)

        if self.__x_offset_calc != 0 or self.__y_offset_calc != 0:

            offset = super().offset()

            super().setOffset(offset.x() + self.__x_offset_calc,
                              offset.y() + self.__y_offset_calc)

    def setXOffsetExpression(self, expression: 'Optional[str]',
                             multiplier: float = 1) -> None:

        if expression is None:
            self.__x_offset_func = None
        else:
            self.__x_offset_func = Expression(expression, default_value=0)

        self.__x_offset_func_mul = multiplier
        self.evaluate()

    def setYOffsetExpression(self, expression: 'Optional[str]',
                             multiplier: float = 1) -> None:

        if expression is None:
            self.__y_offset_func = None
        else:
            self.__y_offset_func = Expression(expression, default_value=0)

        self.__y_offset_func_mul = multiplier
        self.evaluate()

    def setAngleOffsetExpression(self, expression: 'Optional[str]') -> None:

        if expression is None:
            self.__angle_offset_func = None
        else:
            self.__angle_offset_func = Expression(expression, default_value=0)

        self.evaluate()

    def __updateOffset(self, new_calc_x: float, new_calc_y: float) -> None:

        offset = super().offset()

        super().setOffset(
            offset.x() - self.__x_offset_calc + new_calc_x,
            offset.y() - self.__y_offset_calc + new_calc_y)

        self.__x_offset_calc = new_calc_x
        self.__y_offset_calc = new_calc_y

    def evaluate(self, **kwargs: 'Any') -> None:

        self.__condition_met = self.__condition.evaluate(
            **self.__names, **kwargs) if self.__condition is not None else True

        if self.__is_visible:
            super().setVisible(self.__condition_met)

        offset_modif = False

        new_calc_x = 0
        if self.__x_offset_func is not None:
            new_calc_x = self.__x_offset_func.evaluate(
                **self.__names, **kwargs)*self.__x_offset_func_mul
            offset_modif = True

        new_calc_y = 0
        if self.__y_offset_func is not None:
            new_calc_y = self.__y_offset_func.evaluate(
                **self.__names, **kwargs)*self.__y_offset_func_mul
            offset_modif = True

        if offset_modif:
            self.__updateOffset(new_calc_x, new_calc_y)

        if self.__angle_offset_func is not None:
            new_angle = self.__angle_offset_func.evaluate(**self.__names,
                                                          **kwargs)

            if not isclose(self.__angle_offset_calc, new_angle,
                           rel_tol=0, abs_tol=0.5):

                self.__angle_offset_calc = new_angle
                super().setPixmap(self.__pixmap.transformed(
                    QTransform().rotate(new_angle)))

