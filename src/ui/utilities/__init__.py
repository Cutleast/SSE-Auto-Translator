"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget


def move_to_center(widget: QWidget, referent: Optional[QWidget] = None) -> None:
    """
    Moves a widget to the center of the primary screen or,
    if specified, to the center of a referent widget.

    Args:
        widget (QWidget): Widget to move
        referent (Optional[QWidget], optional): Referent widget. Defaults to None.
    """

    size = widget.size()
    w = size.width()
    h = size.height()

    if referent is None:
        rsize = QApplication.primaryScreen().size()
    else:
        rsize = referent.size()

    rw = rsize.width()
    rh = rsize.height()

    x = int((rw / 2) - (w / 2))
    y = int((rh / 2) - (h / 2))

    widget.move(x, y)


def apply_shadow(widget: QWidget, size: int = 4, shadow_color: str = "#181818") -> None:
    """
    Applies standardized shadow effect to a widget.
    Replaces existing graphics effects.

    Args:
        widget (QWidget): Widget to apply shadow
        size (int, optional): Shadow size. Defaults to 4.
        shadow_color (str, optional): Shadow color. Defaults to "#181818".
    """

    shadoweffect = QGraphicsDropShadowEffect(widget)
    shadoweffect.setBlurRadius(size)
    shadoweffect.setXOffset(size)
    shadoweffect.setYOffset(size)
    shadoweffect.setColor(QColor.fromString(shadow_color))
    widget.setGraphicsEffect(shadoweffect)
