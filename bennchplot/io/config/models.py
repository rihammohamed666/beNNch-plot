from pydantic import BaseModel, Field
from pathlib import Path

class SourceConfig(BaseModel):
    host : str
    path : Path | str

class VarConfig(BaseModel):
    path : str
    parser: str

class Config(BaseModel):
    source : SourceConfig
    vars : dict[str, VarConfig]