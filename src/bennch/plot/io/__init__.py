"""
Module for all i/o related code.

In the base of this module, only very general functionality required by
submodules should be implemented. See submodules for specific i/o
functionality.
"""

import logging
from types import ModuleType
from typing import Any
from uuid import UUID

from pydantic import BaseModel, RootModel
from ruamel.yaml import YAML

yaml = YAML()  # This can be globally configured here.
log = logging.getLogger(__name__)


def _str_representer(dumper, data):
    "Represent data as scalars."
    # if isinstance(data, Enum):
    #    # maybe change all to StrEnum (Py>=3.11)
    #    # see https://docs.python.org/3/library/enum.html#enum.StrEnum
    #    return dumper.represent_str(data.name.lower())
    if isinstance(data, ModuleType):
        return dumper.represent_str(data.__name__)
    return dumper.represent_str(str(data))


def represent_str(cls):
    """
    Represent classes as strings in YAML.

    Decorated classes will be registered with the bennch.io YAML backend by
    adding a representer as scalar "tag:yaml.org,2002:str".

    Use this like
    >>> # from bennch.io import yaml, represent_str
    >>> from sys import stdout
    >>> from enum import Enum
    >>> @represent_str
    ... class MyEnum(str, Enum):
    ...     ALLOCATED = "allocated"
    ...     DOWN = "down"
    ...     IDLE = "idle"
    ...     MIXED = "mixed"
    >>> yaml.dump(MyEnum("down"), stream=stdout)
    down
    ...

    This can also be used to wrap builtins
    >>> from pathlib import Path, PosixPath
    >>> represent_str(PosixPath)
    <class 'pathlib.PosixPath'>
    >>> yaml.dump(Path("."), stream=stdout)
    .
    ...
    """
    # this modifies the bennch.io.yaml object!
    yaml.representer.add_representer(cls, _str_representer)
    return cls


# This becomes too complex and needs to be refactored.
def model2dict(obj, id_map=None) -> dict[str, Any]:  # noqa: C901
    """
    Generate a nested dict structure of plain python type from BaseModel.

    from: https://stackoverflow.com/a/71679390

    Note that this is very different from `BaseModel.model_dump()` in at least
    the following points:
    * model_dump is not recursive
    * model_dump does not preserve object identity, this does.
    * model2dict does not respect field aliasses, and other model_dump() flags
    """
    # exclude_defaults = True

    log.debug("model2dict() called on %s %s", type(obj), str(obj))
    if id_map is None:
        id_map = {}
    obj_id = id(obj)
    if obj_id in id_map:
        log.debug("object %s already found translated as %s", obj_id, id_map[obj_id])
        return id_map[obj_id]
    ret_val: Any
    if isinstance(obj, dict):
        log.debug("parse as dict")
        ret_val = {}
        for key, value in obj.items():
            log.debug("key = %s", key)
            log.debug("value = %s", value)
            ret_val[key] = model2dict(value, id_map)
    elif isinstance(obj, RootModel):
        log.debug("parse as RootModel: %s", type(obj))
        ret_val = obj.model_dump()  # use pydantic serializer
    elif isinstance(obj, BaseModel):
        log.debug("parse as BaseModel: %s", type(obj))
        ret_val = {}
        for key in obj.__class__.model_fields:
            log.debug("key = %s", key)
            # log.debug("value = %s", value)
            # Here we can possibly remove entries that have not explicitly been
            # set.
            # if key not in obj.model_fields_set():
            #    continue
            ret_val[key] = model2dict(getattr(obj, key), id_map)
    elif isinstance(obj, UUID):
        log.debug("parse as uuid %s", obj)
        ret_val = str(obj)
    elif isinstance(obj, list):
        log.debug("parse as list")
        ret_val = []
        for elem in obj:
            ret_val.append(model2dict(elem, id_map))
    # Path should be registered with represent_str()
    # elif isinstance(obj, Path):
    #    return str(obj)  # type: ignore[return-value]
    else:  # should be primitive
        return obj
    id_map[obj_id] = ret_val
    return ret_val
