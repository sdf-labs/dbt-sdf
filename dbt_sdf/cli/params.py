from pathlib import Path

import click

workspace_dir = click.option(
    "--workspace-dir",
    envvar="DBT_SDF_WORKSPACE_DIR",
    help="Which directory to output migration artifacts in. If not set, dbt will create a directory called `sdf` in the current working directory.",
    default=Path.cwd(),
    type=click.Path(exists=True),
)