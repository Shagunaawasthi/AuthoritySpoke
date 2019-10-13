"""Nesting fields to prepare to load a dict with a Marshmallow schema."""

from typing import Dict, List


def nest_fields(data: Dict, nest: str, eggs: List[str]):
    """
    Make sure specified fields are nested under "nest" key.
    """
    for egg_field in eggs:
        if egg_field in data:
            if not data.get(nest):
                data[nest] = {}
            data[nest][egg_field] = data.pop(egg_field)
    return data