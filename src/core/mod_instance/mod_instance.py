"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.utilities.container_utils import unique

from .mod import Mod
from .plugin import Plugin


class ModInstance(QObject):
    """
    Class to represent a loaded modlist.
    """

    update_signal = Signal()
    """
    This signal gets emitted everytime, the status of one or more plugins changes.
    """

    display_name: str
    """
    Display name of this instance.
    """

    mods: list[Mod]
    """
    List of all installed mods in this instance.
    """

    __selected_plugins: Optional[list[Plugin]] = None
    __selected_mods: Optional[list[Mod]] = None

    def __init__(self, display_name: str, mods: list[Mod]) -> None:
        super().__init__()

        self.display_name = display_name
        self.mods = mods

    @property
    def plugins(self) -> list[Plugin]:
        """
        List of all installed plugins in this instance.
        """

        return [plugin for mod in self.mods for plugin in mod.plugins]

    @property
    def selected_plugins(self) -> list[Plugin]:
        """
        List of all plugins that are currently selected
        or all plugins if none are selected.
        """

        return self.__selected_plugins or self.plugins

    @selected_plugins.setter
    def selected_plugins(self, value: Optional[list[Plugin]]) -> None:
        self.__selected_plugins = value

    @property
    def selected_mods(self) -> list[Mod]:
        """
        List of all mods that are currently selected
        or all mods if none are selected.
        """

        return self.__selected_mods or self.mods

    @selected_mods.setter
    def selected_mods(self, value: Optional[list[Mod]]) -> None:
        self.__selected_mods = value

    @property
    def selected_items(self) -> dict[Mod, list[Plugin]]:
        """
        Dictionary of mods and their plugins that are currently selected.
        """

        return {
            mod: [plugin for plugin in mod.plugins if plugin in self.selected_plugins]
            for mod in self.selected_mods
        }

    def get_plugin(
        self,
        plugin_name: str,
        ignore_mods: list[Mod] = [],
        ignore_states: list[Plugin.Status] = [],
        ignore_case: bool = False,
    ) -> Optional[Plugin]:
        """
        Get a plugin by its name or None if it doesn't exist.
        Returns the plugin with the highest index if there are
        multiple plugins with the same name.

        Args:
            plugin_name (str): Name of the plugin
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[Plugin.Status], optional):
                List of plugin states to ignore. Defaults to [].
            ignore_case (bool, optional): Whether to ignore case. Defaults to False.

        Returns:
            Optional[Plugin]: Plugin or None
        """

        mods: dict[Mod, Plugin] = {
            mod: plugin
            for mod in self.mods
            for plugin in mod.plugins
            if plugin.name == plugin_name
            or (ignore_case and plugin.name.lower() == plugin_name.lower())
            and mod not in ignore_mods
            and plugin.status not in ignore_states
        }

        # Get the plugin from the mod with the highest modlist index
        return max(
            mods.items(),
            key=lambda item: self.mods.index(item[0]),
            default=(None, None),
        )[1]

    def get_mod_with_plugin(
        self,
        plugin_name: str,
        ignore_mods: list[Mod] = [],
        ignore_states: list[Plugin.Status] = [],
        ignore_case: bool = False,
    ) -> Optional[Mod]:
        """
        Get a mod that has the specified plugin or None if it doesn't exist.
        Returns the mod with the highest index if there are
        multiple mods with the same plugin.

        Args:
            plugin_name (str): Name of the plugin
            ignore_mods (list[Mod], optional): List of mods to ignore. Defaults to [].
            ignore_states (list[Plugin.Status], optional):
                List of plugin states to ignore. Defaults to [].
            ignore_case (bool, optional): Whether to ignore case. Defaults to False.

        Returns:
            Optional[Mod]: Mod or None
        """

        mods: list[Mod] = unique(
            mod
            for mod in filter(lambda m: m not in ignore_mods, self.mods)
            for plugin in filter(lambda p: p.status not in ignore_states, mod.plugins)
            if plugin.name == plugin_name
            or (ignore_case and plugin.name.lower() == plugin_name.lower())
        )

        # Get the mod with the highest modlist index
        return max(mods, key=lambda m: self.mods.index(m), default=None)  # type: ignore[arg-type]

    def get_plugin_state_summary(
        self, plugins: Optional[list[Plugin]] = None
    ) -> dict[Plugin.Status, int]:
        """
        Gets a summary of the plugin states.

        Args:
            plugins (Optional[list[Plugin]], optional):
                List of plugins to count. Defaults to the entire modlist.

        Returns:
            dict[Plugin.Status, int]: Summary of the plugin states
        """

        plugins = plugins or self.plugins

        return {
            state: len([plugin for plugin in plugins if plugin.status == state])
            for state in Plugin.Status
        }

    def load_plugin_states_from_cache(self) -> dict[Plugin, bool]:
        """
        Loads the plugin states from the cache and applies them.

        Returns:
            dict[Plugin, bool]: Dictionary of plugins and their checkstate.
        """

        cacher: Cacher = AppContext.get_app().cacher
        check_state: dict[Plugin, bool] = {}

        for mod in self.mods:
            for plugin in mod.plugins:
                checked, plugin.status = cacher.get_from_plugin_states_cache(
                    plugin.path
                ) or (True, plugin.Status.NoneStatus)
                check_state[plugin] = checked

        self.update_signal.emit()

        return check_state

    def set_plugin_states(self, states: dict[Plugin, Plugin.Status]) -> None:
        """
        Applies the given plugin states to the modlist and emits the update signal.

        Args:
            states (dict[Plugin, Plugin.Status]): Dictionary of plugins and their states
        """

        for plugin, state in states.items():
            plugin.status = state

        self.update_signal.emit()
