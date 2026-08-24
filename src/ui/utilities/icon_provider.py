"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from enum import Enum
from typing import ClassVar

from cutleast_core_lib.ui.theme.models.types import ThemeAlias
from cutleast_core_lib.ui.utilities.icon_provider import (
    IconProvider as BaseIconProvider,
)
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon


class ResourceIcon(Enum):
    """Enum for icons from the resource file."""

    _value_: tuple[str, bool]

    Confrerie = ("cdt", True)
    DetectLang = ("detect_lang", True)
    SSEAT = ("icon", False)
    NexusMods = ("nexus_mods", False)
    OpenInBrowser = ("open_in_browser", True)
    Plugin = ("plugin", True)
    ScanOnline = ("scan_online", True)


class IconProvider(BaseIconProvider):
    """
    Icon provider for SSE-AT specific icons.
    """

    RESOURCE_PREFIX: ClassVar[str] = ":/sse-at/icons"
    """The resource directory containing SSE Auto Translator icons."""

    @classmethod
    def get_res_icon(
        cls,
        resource_icon: ResourceIcon,
        /,
        *,
        color: ThemeAlias = BaseIconProvider.Color.Text,
        color_disabled: ThemeAlias = BaseIconProvider.Color.Secondary,
        color_active: ThemeAlias = BaseIconProvider.Color.Text,
        color_selected: ThemeAlias = BaseIconProvider.Color.Primary,
        color_on: ThemeAlias = BaseIconProvider.Color.Primary,
    ) -> QIcon:
        """
        Gets the specified icon from the resource file and returns it.

        Args:
            resource_icon (ResourceIcon): The icon to get.
            color (ThemeAlias, optional): The icon color. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional): The disabled icon color. Defaults
                to Color.Secondary.
            color_active (ThemeAlias, optional): The active icon color. Defaults to
                Color.Text.
            color_selected (ThemeAlias, optional): The selected icon color. Defaults
                to Color.Primary.
            color_on (ThemeAlias, optional): The checked icon color. Defaults to
                Color.Primary.

        Raises:
            FileNotFoundError: When the icon does not exist.

        Returns:
            QIcon: The icon.
        """

        return cls.get_icon(
            resource_icon.value[0],
            set_colors=resource_icon.value[1],
            color=color,
            color_disabled=color_disabled,
            color_active=color_active,
            color_selected=color_selected,
            color_on=color_on,
            resource_prefix=cls.RESOURCE_PREFIX,
        )

    @classmethod
    def bind_res_icon(
        cls,
        target: QObject,
        consumer: Callable[[QIcon], None],
        resource_icon: ResourceIcon,
        /,
        *,
        color: ThemeAlias = BaseIconProvider.Color.Text,
        color_disabled: ThemeAlias = BaseIconProvider.Color.Secondary,
        color_active: ThemeAlias = BaseIconProvider.Color.Text,
        color_selected: ThemeAlias = BaseIconProvider.Color.Primary,
        color_on: ThemeAlias = BaseIconProvider.Color.Primary,
    ) -> BaseIconProvider.ThemeIconBinding:
        """
        Binds an SSE Auto Translator resource icon to an icon consumer.

        Args:
            target (QObject): The target QObject.
            consumer (Callable[[QIcon], None]): Applies the generated icon.
            resource_icon (ResourceIcon): The SSE Auto Translator icon to bind.
            color (ThemeAlias, optional): The icon color. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional): The disabled icon color. Defaults
                to Color.Secondary.
            color_active (ThemeAlias, optional): The active icon color. Defaults to
                Color.Text.
            color_selected (ThemeAlias, optional): The selected icon color. Defaults
                to Color.Primary.
            color_on (ThemeAlias, optional): The checked icon color. Defaults to
                Color.Primary.

        Returns:
            BaseIconProvider.ThemeIconBinding: The theme-aware icon binding.
        """

        return cls.bind_icon(
            target,
            consumer,
            resource_icon.value[0],
            set_colors=resource_icon.value[1],
            color=color,
            color_disabled=color_disabled,
            color_active=color_active,
            color_selected=color_selected,
            color_on=color_on,
            resource_prefix=cls.RESOURCE_PREFIX,
        )
