"Data models for configuration files."

from pathlib import Path

from pydantic import BaseModel


class SourceConfig(BaseModel):
    "Define a source location for the UUID tarballs."

    host: str
    path: Path | str


class VarConfig(BaseModel):
    """
    Extractor config for bash stdio stream parsers.

    The found `path`s (wildcards allowed, see man tar) will be directly
    streamed to stdin of `parser` command on the shell.
    """

    path: str
    parser: str


class Config(BaseModel):
    "Top-level configuration file format."

    source: SourceConfig
    vars: dict[str, VarConfig]
