"Different views are collected here."

from pydantic import BaseModel
from rich.console import Console
from rich.syntax import Syntax

console = Console()


def rich_view(_ctx, result, **_) -> None:
    "Give a user readable highlighted output."
    if isinstance(result, BaseModel):
        console.print(Syntax(result.model_dump_json(indent=2), "json", background_color="default"))
    else:
        console.print(result)
