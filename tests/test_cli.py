from dbt_sdf.cli.main import cli


def test_cli():
    assert cli() == None