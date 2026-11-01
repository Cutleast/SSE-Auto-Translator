"""
Copyright (c) Cutleast
"""


class ReleaseError(RuntimeError):
    """
    Raised when release metadata, the Git state or the Nexus Mods state does not allow
    publishing a release.
    """


class RetryableReleaseError(ReleaseError):
    """
    Raised for temporary failures that may succeed when retried.
    """
