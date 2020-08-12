"""
box_classification SQL table model and manager
"""

import logging
from typing import List
import time

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy import func as sql_func

from src.sql import sql


log = logging.getLogger(__name__)


class BoxClassification(sql.model):
    """
    box_classification SQL table model
    """

    __tablename__ = "box_classification"

    ID = Column(Integer, primary_key=True, autoincrement=True)
    BOX_FILE_ID = Column(String)
    BOX_FILE_NAME = Column(String)
    BOX_FILE_OWNER = Column(String)
    BOX_CLASSIFICATION_NAME = Column(String)
    MCAS_POLICY_ID = Column(String)
    APPLIED = Column(Boolean)
    APPLY_ATTEMPTS = Column(Integer)
    APPLY_ERROR_EXCEPTION_MESSAGE = Column(Text)
    APPLY_ERROR_FORBIDDEN = Column(Boolean)
    APPLY_ERROR_NO_BOX_USER = Column(Boolean)
    CREATED = Column(DateTime, default=sql_func.now())
    UPDATED = Column(DateTime, default=sql_func.now(), onupdate=sql_func.now())

    def __str__(self):
        return f"<{type(self).__name__}:{self.BOX_FILE_ID}:{self.BOX_CLASSIFICATION_NAME}>"


class BoxClassificationSQLManager(sql.SQLManager):
    """
    box_classification SQL table manager
    """

    model = BoxClassification

    def new_record(
            self,
            box_file_id,
            box_file_name,
            box_file_owner,
            box_classification_name,
            mcas_policy_id,
    ) -> BoxClassification:
        """
        Inserts a new box_classification record
        """
        record = self.model(
            BOX_FILE_ID=box_file_id,
            BOX_FILE_NAME=box_file_name,
            BOX_FILE_OWNER=box_file_owner,
            BOX_CLASSIFICATION_NAME=box_classification_name,
            MCAS_POLICY_ID=mcas_policy_id,
            APPLIED=False,
            APPLY_ATTEMPTS=1
        )
        log.info(f"built {self.model.__tablename__} record {record}")

        return record

    def failed_apply_retry_records(self) -> List[BoxClassification]:
        """
        Returns a SQL result set of box_classification records for retrying failed sync to from MCAS to Box
        """
        return self.model_query.filter(
            self.model.APPLIED == False,
            self.model.APPLY_ERROR_FORBIDDEN == None,
            self.model.APPLY_ERROR_NO_BOX_USER == None,
            self.model.APPLY_ATTEMPTS < 10
        )
