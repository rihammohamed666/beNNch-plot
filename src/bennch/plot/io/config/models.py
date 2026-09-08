"Data models for configuration files."

from pathlib import Path

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    "Define a source location for the UUID tarballs."

    host: str = Field()
    path: Path | str = Field()


class VarConfig(BaseModel):
    """
    Extractor config for bash stdio stream parsers.

    The found `path`s (wildcards allowed, see man tar) will be directly
    streamed to stdin of `parser` command on the shell.
    """

    path: str
    parser: str
    cast: str = Field(default="str", description="call a transfrom function after loading the value")


class CurrentSet(BaseModel):
    "Currently active set of UUIDs."

    setid: str = Field(
        default="d751713988987e9331980363e24189ce",
        description="key of current UUIDset. Default is the hash of an empty set.",
    )


class Config(BaseModel):
    "Top-level configuration file format."

    source: SourceConfig = Field(default_factory=SourceConfig.model_validate)
    vars: dict[str, VarConfig] = Field(default_factory=dict)
    current_set: CurrentSet = Field(default_factory=CurrentSet)
