"""
Copyright (c) Cutleast
"""

from typing import Optional


class AppContext:
    """
    Singleton context for storing the main application instance.
    """

    _app_instance: Optional["App"] = None

    @classmethod
    def get_app(cls) -> "App":
        """
        Returns the main application instance.

        Raises:
            RuntimeError: when the application instance has not been initialized.

        Returns:
            App: The main application instance
        """

        if cls._app_instance is None:
            raise RuntimeError("The application instance has not been initialized.")
        return cls._app_instance

    @classmethod
    def set_app(cls, app: "App") -> None:
        """
        Sets the main application instance.

        Args:
            app (App): The main application instance

        Raises:
            RuntimeError: when the application instance is already set.
        """

        if cls._app_instance is not None:
            raise RuntimeError("The application instance is already set.")
        cls._app_instance = app

    @classmethod
    def get_app_type(cls) -> type["App"]:
        from app import App

        return App


if __name__ == "__main__":
    from app import App
