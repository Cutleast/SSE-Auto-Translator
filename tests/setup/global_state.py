"""
Copyright (c) Cutleast
"""

import logging
from collections.abc import Iterator
from typing import Any, Optional

from cutleast_core_lib.core.cache.function_cache import FunctionCache
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.test.utils import Utils
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget


class GlobalState:
    """
    Resets process-wide state that the application keeps outside of its objects, so
    that tests cannot influence each other.

    This works without any test-specific changes to the production code by discovering
    all singleton classes via `type.__subclasses__()`.
    """

    log: logging.Logger = logging.getLogger("GlobalState")

    @staticmethod
    def iter_singleton_classes() -> Iterator[type[Singleton]]:
        """
        Iterates over all (direct and indirect) subclasses of `Singleton` that are
        currently imported.

        Yields:
            type[Singleton]: A singleton class.
        """

        pending: list[type[Singleton]] = list(Singleton.__subclasses__())
        seen: set[type[Singleton]] = set()
        while pending:
            singleton_cls: type[Singleton] = pending.pop()
            if singleton_cls in seen:
                continue

            seen.add(singleton_cls)
            pending.extend(singleton_cls.__subclasses__())
            yield singleton_cls

    @staticmethod
    def get_own_instance(singleton_cls: type[Singleton]) -> Any:
        """
        Gets the instance that is stored for exactly the specified singleton class and
        not inherited from one of its base classes.

        Args:
            singleton_cls (type[Singleton]): The singleton class.

        Returns:
            Any: The instance or `None` if there is none.
        """

        field_name: str = f"_Singleton__{Utils.SINGLETON_INSTANCE[0]}"

        return vars(singleton_cls).get(field_name)

    @staticmethod
    def reset_singletons(keep: frozenset[type[Singleton]]) -> list[str]:
        """
        Resets all initialized singletons except the specified ones.

        Args:
            keep (frozenset[type[Singleton]]): Singleton classes to keep initialized.

        Returns:
            list[str]: The names of the singleton classes that were reset.
        """

        field_name: str = f"_Singleton__{Utils.SINGLETON_INSTANCE[0]}"
        reset_classes: list[str] = []
        for singleton_cls in GlobalState.iter_singleton_classes():
            if singleton_cls in keep:
                continue

            instance: Any = GlobalState.get_own_instance(singleton_cls)
            if instance is None:
                continue

            if isinstance(instance, Logger):
                GlobalState.close_logger(instance)

            setattr(singleton_cls, field_name, None)
            reset_classes.append(singleton_cls.__qualname__)

        return reset_classes

    @staticmethod
    def close_logger(logger: Logger) -> None:
        """
        Closes the specified application logger and detaches it from the root logger,
        `sys.stdout` and `sys.stderr`.

        Args:
            logger (Logger): The logger to close.
        """

        for handler in list(logging.root.handlers):
            if getattr(handler, "stream", None) is logger:
                logging.root.removeHandler(handler)

        logger.close()

    @staticmethod
    def clear_function_cache() -> None:
        """
        Clears the process-wide cache of `FunctionCache`.
        """

        cache: dict[str, Any] = vars(FunctionCache)["_FunctionCache__cache"]
        cache.clear()

    @staticmethod
    def delete_widgets() -> None:
        """
        Closes and deletes all top-level widgets. Closing alone (as done by `qtbot`)
        keeps the widgets and their timers alive, which then fire in later tests.
        """

        app: Optional[QCoreApplication] = QApplication.instance()
        if not isinstance(app, QApplication):
            return

        widgets: list[QWidget] = QApplication.topLevelWidgets()
        for widget in widgets:
            widget.close()
            widget.deleteLater()

        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
