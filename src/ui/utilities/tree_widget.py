"""
Copyright (c) Cutleast
"""

from collections.abc import Generator

from PySide6.QtWidgets import QTreeWidgetItem


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
            return are_children_visible(child)
        elif not child.isHidden():
            return True

    return False
