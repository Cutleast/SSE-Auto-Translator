"""
Copyright (c) Cutleast
"""


def scale_value(value: int | float, unit: str = "B", factor: int = 1024) -> str:
    """
    Scales a value to its proper format with a unit and a factor as
    scaling and returns it as string; for e.g:

        1253656 => '1.20 MB'

        1253656678 => '1.17 GB'

    Args:
        value (int | float): Value to scale.
        unit (str, optional): Unit suffix. Defaults to "B" (Bytes).
        factor (int, optional): Scaling factor. Defaults to 1024 (Bytes).

    Returns:
        str: Scaled value with unit and scale suffix.
    """

    for suffix in ["", "K", "M", "G", "T", "P", "H"]:
        if abs(value) < factor:
            if f"{value:.2f}".split(".")[1] == "00":
                return f"{int(value)} {suffix}{unit}"

            return f"{value:.2f} {suffix}{unit}"

        value /= factor

    return str(value)
