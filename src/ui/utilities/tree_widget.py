"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from typing import Optional

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


def iter_children(item: QTreeWidgetItem) -> Generator[QTreeWidgetItem]:
    """
    Iterates over all children of a tree item.

    Args:
        item (QTreeWidgetItem): Tree item

    Yields:
        Generator[QTreeWidgetItem]: Tree items
    """

    for i in range(item.childCount()):
        yield item.child(i)


def iter_toplevel_items(widget: QTreeWidget) -> Generator[QTreeWidgetItem]:
    """
    Iterates over all top level items of a tree widget.

    Args:
        widget (QTreeWidget): Tree widget

    Yields:
        Generator[QTreeWidgetItem]: Tree items
    """

    for i in range(widget.topLevelItemCount()):
        item: Optional[QTreeWidgetItem] = widget.topLevelItem(i)
        if item is not None:
            yield item


def are_children_visible(item: QTreeWidgetItem) -> bool:
    """
    Checks if any child of a tree item or its children is visible.

    Args:
        item (QTreeWidgetItem): Tree item

    Returns:
        bool: True if any child is visible, False otherwise
    """

    for child in iter_children(item):
        if child.childCount() > 0:
            if not child.isHidden() or are_children_visible(child):
                return True
        elif not child.isHidden():
            return True

    return False
