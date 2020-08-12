"""
Application entry point
"""

import click

from src.commands import (
    mcas,
    sql,
    process
)


@click.group()
def cli() -> None:
    """
    Click application group to support multiple commands
    """
    pass


def main() -> None:
    """
    Main application function. Registers Click CLI commands to a group, then runs the Click application.
    """
    commands = [
        mcas.mcas_policy_box_classification_sync,
        sql.sql_create_database,
        sql.sql_create_table,
        sql.sql_drop_table,
        process.kill_pythonw_process
    ]
    for command in commands:
        cli.add_command(command)

    cli()


if __name__ == "__main__":
    main()
