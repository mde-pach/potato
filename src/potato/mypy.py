"""Potato Mypy Plugin - delegates to Pydantic's mypy plugin.

Validation is now performed at runtime during class definition
(in ViewDTOMeta and AggregateMeta metaclasses).
"""

from pydantic.mypy import PydanticPlugin


def plugin(version: str):
    return PydanticPlugin
