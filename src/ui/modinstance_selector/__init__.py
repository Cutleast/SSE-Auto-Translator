"""
Copyright (c) Cutleast
"""

from .base_selector_widget import BaseSelectorWidget
from .modorganizer_selector_widget import ModOrganizerSelectorWidget
from .vortex_selector_widget import VortexSelectorWidget

INSTANCE_WIDGETS: list[type[BaseSelectorWidget]] = [
    VortexSelectorWidget,
    ModOrganizerSelectorWidget,
]
"""
List of available instance widgets.
"""
