"""
SQLAlchemy utilities for an interface into a SQL database
"""

import logging

from abc import ABCMeta, abstractmethod

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


log = logging.getLogger(__name__)


connection = None
model = declarative_base()


def configure_connection(config: dict) -> None:
    """
    Connects to a SQL database defined in a configuration dictionary and set the connection as a global variable
    """
    global connection
    sql_config = config["sql"]
    if sql_config['driver'] == "mssql+pyodbc":
        connection_string = f"{sql_config['driver']}://{sql_config['username']}:{sql_config['password']}@{sql_config['host']}:{sql_config['port']}/{sql_config['database']}?driver=ODBC+Driver+17+for+SQL+Server;Encrypt=yes;TrustServerCertificate=no;"
    else:
        connection_string = f"{sql_config['driver']}://{sql_config['username']}:{sql_config['password']}@{sql_config['host']}:{sql_config['port']}/{sql_config['database']}"
    print(connection_string)
    connection = create_engine(connection_string)
    log.debug(f"connected to SQL database {sql_config['host']}")


class SQLManager(metaclass=ABCMeta):
    """
    SQLAlchemy model manager abstract class with query utilities
    """

    def __init__(self, sql_connection):
        self.session = self.session_from_connection(sql_connection)

    @property
    @abstractmethod
    def model(self):
        """
        SQLAlchemy model class
        """
        pass

    @staticmethod
    def session_from_connection(sql_connection):
        """
        Returns a thread safe SQL session from a SQL connection object
        """
        return scoped_session(sessionmaker(bind=sql_connection))()

    def insert(self, **kwargs):
        """
        Inserts a SQL record
        """
        record = self.model(**kwargs)
        self.update(record)
        log.info(f"inserted {record}")

        return record

    def commit(self):
        """
        Commits a SQL session
        """
        try:
            self.session.commit()
            log.info(f"committed SQL session")
        except Exception as e:
            self.session.rollback()
            raise e

    def update(self, record, commit=True):
        """
        Updates a SQL record
        """
        self.session.add(record)
        log.info(f"added obj {record} to SQL session")
        if commit:
            self.commit()

    def get(self, **kwargs):
        """
        Gets a SQL record
        """
        return self.get_all(**kwargs).first()

    def get_all(self, start_index=None, end_index=None, **kwargs):
        """
        Gets a SQL record result set
        """
        if start_index and end_index:
            records = self.model_query.filter_by(**kwargs)[start_index:end_index]
        else:
            records = self.model_query.filter_by(**kwargs)

        return records

    def get_all_order_by(self, order_by, **kwargs):
        """
        Gets an ordered SQL record result set
        """
        return self.model_query.filter_by(**kwargs).order_by(order_by)

    def exists(self, **kwargs):
        """
        Checks if a SQL record exists
        """
        return self.get(**kwargs) is not None

    def delete(self, record):
        """
        Deletes a SQL record
        """
        self.session.delete(record)
        self.commit()

    def delete_all(self, **kwargs):
        """
        Deletes records from a SQL result set
        """
        records = self.get_all(**kwargs)
        for record in records:
            self.delete(record)

    def bulk_update(self, records):
        """
        Updates a list of SQL records
        """
        for record in records:
            self.update(record, commit=False)
        self.commit()

    @property
    def model_query(self):
        """
        Returns a SQL query builder
        """
        return self.session.query(self.model)
