from bennchplot.io.config.models import VarConfig, SourceConfig
from subprocess import check_call

def get_variable_value(uuid: str, var: VarConfig, source: SourceConfig) -> None:
    "Get the triggering pipeline ID of the given simulation."
    tar = f'tar --wildcards -zxOf { uuid }.tgz {var.path}'
    check_call(f"ssh {source.host} 'cd {source.path}; { tar } | {var.parser}'", shell=True)
