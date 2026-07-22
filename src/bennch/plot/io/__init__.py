"""
Module for all i/o related code.

In the base of this module, only very general functionality required by
submodules should be implemented. See submodules for specific i/o
functionality.
"""

from ruamel.yaml import YAML

yaml = YAML()  # This can be globally configured here.
