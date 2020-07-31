"""
Click commands for interfacing with a box_classification SQL table
"""

import logging

import click
from sqlalchemy_utils import create_database

from src import config
from src.sql.models.box_classification import BoxClassification
from src.sql import sql


log = logging.getLogger(__name__)


@click.command()
@click.option(
    "-e", "--env", default="prod", help="env environment alias", type=str,
)
@config.config_env
def sql_create_database(env, config):
    """
    Creates a SQL database
    """
    sql.configure_connection(config)
    create_database(sql.connection.url)
    log.info("Created SQL box_mcas database")


@click.command()
@click.option(
    "-e", "--env", default="prod", help="env environment alias", type=str,
)
@config.config_env
def sql_create_table(env, config):
    """
    Creates a SQL box_classification table
    """
    sql.configure_connection(config)
    sql.model.metadata.create_all(sql.connection)
    log.info("Created SQL classification_assign table")


@click.command()
@click.option(
    "-e", "--env", default="prod", help="env environment alias", type=str,
)
@config.config_env
def sql_drop_table(env, config):
    """
    Drops a SQL box_classification table
    """
    while True:
        y_n = input(
            "\nAre you sure you want to drop the SQL box_classification table? (Y/N): "
        ).lower()
        if y_n == "y":
            break
        elif y_n == "n":
            exit()
        else:
            print("Invalid input")

    sql.configure_connection(config)
    BoxClassification.__table__.drop(sql.connection)
    log.info("Dropped SQL box_classification_apply table")
