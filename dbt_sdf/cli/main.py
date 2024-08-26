
import functools
import yaml
from copy import copy
from dataclasses import dataclass
from typing import Callable, List, Optional, Union
from dbt.contracts.graph.manifest import Manifest

import click
import dbt.cli.params as p
import dbt_sdf.cli.params as sdf_p
from dbt_sdf.schema.generated.models import (
    Workspace,
    Definition
)
from dbt.cli import requires
from dbt.cli.main import global_flags


# dbt-sdf
@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=True,
    epilog="Run `dbt-sdf [command] --help` for more information on a specific command.",
)
@click.pass_context
@global_flags
@p.warn_error
@p.warn_error_options
@p.log_format
@p.show_resource_report
def cli(ctx, **kwargs):
    """A migration tool for dbt models."""

# dbt-sdf migrate
@cli.command("migrate")
@click.pass_context
@global_flags
@p.profile
@p.profiles_dir
@p.project_dir
@p.target
@p.target_path
@p.threads
@p.vars
@sdf_p.workspace_dir
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest()
def migrate(ctx, **kwargs):
    """Migrates a dbt project to an SDF Workspace."""
    # manifest generation and writing happens in @requires.manifest
    print(ctx)
    manifest: Manifest = ctx.obj["manifest"]
    # Iterate over the nodes in the manifest, reading the SQL, replacing sources, refs, config blocks, and writing to a new file
    
    # Get all the conventions from the current initializer, including for credentials
    workspace = Workspace(
        edition="1.3",
        name="demo_name"
    )
    definition = Definition(
        workspace=workspace
    )
    
    # Write the workspace to the workspace directory
    with open("workspace.sdf.yml", "w") as yaml_file:
        yaml.dump(definition.model_dump(exclude_defaults=True), yaml_file, default_flow_style=False)

    return None, True