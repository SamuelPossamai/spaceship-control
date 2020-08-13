
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItemGroup
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt

from .conditiongraphicspixmapitem import ConditionGraphicsPixmapItem
from .objectgraphicsitem import ObjectGraphicsItem

from ..storage.fileinfo import FileInfo

from ..utils.expression import Expression

if TYPE_CHECKING:
    from typing import Tuple

def __getSizeScale(cur_width: float, cur_height: float, after_width: float,
                   after_height: float) -> 'Tuple[float, float]':

    width_scale: float
    height_scale: float

    width_scale = height_scale = 1
    if after_height is None:
        if after_width is not None:
            width_scale = height_scale = after_width/cur_width
    elif after_width is None:
        width_scale = height_scale = after_height/cur_height
    else:
        width_scale = after_width/cur_width
        height_scale = after_height/cur_height

    return width_scale, height_scale

def __loadGraphicItemImagePart(image, condition_variables,
                               condition_graphic_items):

    pixmap = QPixmap(str(
        FileInfo().getPath(FileInfo.FileDataType.IMAGE, image.name)))

    image_x_is_expr = isinstance(image.x, str)
    image_y_is_expr = isinstance(image.y, str)
    image_angle_is_expr = isinstance(image.angle, str)

    width_scale, height_scale = __getSizeScale(
        pixmap.width(), pixmap.height(), image.width, image.height)

    if not image_angle_is_expr:
        pixmap = pixmap.transformed(QTransform().rotate(image.angle))

    setup_script = image.setup_script
    if setup_script is not None:
        expression = Expression(setup_script)

        if condition_variables:
            expression.evaluate(**condition_variables)
        else:
            expression.evaluate()

        if expression.context:
            condition_variables = expression.context

    if image_angle_is_expr or image_x_is_expr or image_y_is_expr or \
        image.condition:

        gitem_part = ConditionGraphicsPixmapItem(
            image.condition, pixmap,
            names=condition_variables)
        condition_graphic_items.append(gitem_part)
    else:
        gitem_part = QGraphicsPixmapItem(pixmap)

    gitem_part.setTransform(QTransform().scale(width_scale, height_scale))

    if image_angle_is_expr:
        gitem_part.setAngleOffsetExpression(image.angle)

    x_offset = 0
    if image_x_is_expr:
        gitem_part.setXOffsetExpression(image.x, multiplier=1/width_scale)
    else:
        x_offset = image.x/width_scale

    y_offset = 0
    if image_y_is_expr:
        gitem_part.setYOffsetExpression(image.y, multiplier=1/height_scale)
    else:
        y_offset = image.y/height_scale

    gitem_part.setOffset(x_offset - pixmap.width()/2,
                            y_offset - pixmap.height()/2)

    gitem_part.setZValue(image.z_value)

    return gitem_part

def loadGraphicItem(shapes, images, condition_variables=None,
                    default_color=Qt.blue, group_z_value=0):

    if not images:
        if shapes is None:
            return None, ()

        gitem = ObjectGraphicsItem(shapes, color=default_color)
        gitem.setZValue(group_z_value)

        return gitem, ()

    gitem = QGraphicsItemGroup()
    gitem.setZValue(group_z_value)

    condition_graphic_items = []
    for image in images:
        gitem.addToGroup(__loadGraphicItemImagePart(
            image, condition_variables, condition_graphic_items))

    return gitem, condition_graphic_items
