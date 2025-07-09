"""
Copyright (c) Cutleast
"""

import re
from os import getenv
from pathlib import Path
from typing import Optional, overload


@overload
def resolve(text: str, sep: tuple[str, str] = ("%", "%"), **vars: str) -> str:
    """
    Resolves all (environment) variables in a string.

    Args:
        text (str): String with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        str: String with resolved variables
    """


@overload
def resolve(path: Path, sep: tuple[str, str] = ("%", "%"), **vars: str) -> Path:
    """
    Resolves all (environment) variables in a path.

    Args:
        path (Path): Path with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        Path: Resolved real path
    """


def resolve_path(path: Path, sep: tuple[str, str] = ("%", "%"), **vars: str) -> Path:
    """
    Resolves all (environment) variables in a path.

    Args:
        path (Path): Path with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        Path: Resolved real path
    """

    # Lower keys of additional vars (environment vars are already case-insensitive)
    norm_vars: dict[str, str] = {key.lower(): value for key, value in vars.items()}

    pattern: re.Pattern[str] = re.compile(f"^{sep[0]}([a-zA-Z0-9_]*){sep[1]}$")
    parts: list[str] = []
    for part in path.parts:
        match: Optional[re.Match[str]] = pattern.match(part)

        if match is not None:
            var_name: str = match.groups()[0]
            var_value: Optional[str] = norm_vars.get(var_name.lower(), getenv(var_name))
            if var_value is not None:
                parts.append(var_value)
            else:
                parts.append(part)
        else:
            parts.append(part)

    return Path().joinpath(*parts)


def resolve_str(text: str, sep: tuple[str, str] = ("%", "%"), **vars: str) -> str:
    """
    Resolves all (environment) variables in a string.

    Args:
        text (str): String with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        str: Resolved string
    """

    # Lower keys of additional vars (environment vars are already case-insensitive)
    norm_vars: dict[str, str] = {key.lower(): value for key, value in vars.items()}

    pattern: re.Pattern[str] = re.compile("%([a-zA-Z0-9_]*)%")
    matches: list[re.Match[str]] = list(pattern.finditer(text))
    for match in matches:
        var_name: str = match.groups()[0]
        var_value: Optional[str] = norm_vars.get(var_name.lower(), getenv(var_name))
        if var_value is not None:
            text = text.replace(f"%{var_name}%", var_value, 1)

    return text


def resolve(  # type: ignore
    text_or_path: str | Path, sep: tuple[str, str] = ("%", "%"), **vars: str
) -> str | Path:
    if isinstance(text_or_path, Path):
        return resolve_path(text_or_path, sep, **vars)
    else:
        return resolve_str(text_or_path, sep, **vars)
