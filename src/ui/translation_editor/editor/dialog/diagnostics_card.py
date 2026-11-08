"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from typing import Optional

from cutleast_core_lib.core.utilities.typing_utils import coalesce
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from pydantic import BaseModel
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.editor.models import Severity
from ui.utilities.icon_provider import IconProvider


class DiagnosticsCard(QFrame):
    """
    Card displaying information about a diagnostic issue and optionally a quick fix
    button.
    """

    class DiagnosticsIssue(BaseModel, frozen=True, arbitrary_types_allowed=True):
        """
        The issue that is displayed.
        """

        title: str
        """The issue title."""

        description: str
        """The issue description."""

        severity: Severity
        """The issue severity."""

        quick_fix_action: Optional[Callable[[], None]] = None
        """An action to perform, when the quick fix button is clicked."""

        quick_fix_text: Optional[str] = None
        """The text of the quick fix button, if a quick fix is available."""

        custom_widget: Optional[QWidget] = None
        """A custom widget that is displayed next to the quick fix button."""

    __issue: DiagnosticsIssue

    __vlayout: QVBoxLayout
    __quick_fix_button: QPushButton

    def __init__(self, issue: DiagnosticsIssue) -> None:
        """
        Args:
            issue (DiagnosticsIssue): The issue that is represented by this card.
        """

        super().__init__()

        self.__issue = issue

        self.__init_ui()

        if self.__issue.quick_fix_action is not None:
            self.__quick_fix_button.clicked.connect(self.__issue.quick_fix_action)
        else:
            self.__quick_fix_button.hide()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_body()
        self.__init_footer()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        IconProvider.bind_custom_icon(
            icon_label,
            lambda icon: icon_label.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon,
                    ThemeManager.get().theme.metrics.icon,
                )
            ),
            self.__issue.severity.get_icon,
        )
        icon_label.setToolTip(self.__issue.severity.get_localized_name())
        hlayout.addWidget(icon_label)

        title_label = ElidedLabel(self.__issue.title)
        title_label.setProperty("emphasized", True)
        hlayout.addWidget(title_label, stretch=1)

    def __init_body(self) -> None:
        description_label = QLabel(self.__issue.description)
        description_label.setTextFormat(Qt.TextFormat.RichText)
        description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        description_label.setCursor(Qt.CursorShape.IBeamCursor)
        description_label.setWordWrap(True)
        self.__vlayout.addWidget(description_label)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__vlayout.addLayout(hlayout)

        self.__quick_fix_button = QPushButton(coalesce(self.__issue.quick_fix_text, ""))
        hlayout.addWidget(self.__quick_fix_button)

        if self.__issue.custom_widget is not None:
            hlayout.addWidget(self.__issue.custom_widget)

    @property
    def issue(self) -> DiagnosticsIssue:
        """The issue of this card."""

        return self.__issue
