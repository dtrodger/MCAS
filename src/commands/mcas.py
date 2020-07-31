"""
Click command and utilities for a Microsoft Cloud App Security DLP file policy trigger to Box file classification sync
"""

import logging
import json
from typing import Dict, List
import datetime

import click

from src import config as config_utils
from src import box
from src import mcas
from src import thread
from src.sql import sql
from src.sql.models.box_classification import (
    BoxClassification,
    BoxClassificationSQLManager
)
from src.http_utils import RateLimiter


log = logging.getLogger(__name__)


def box_classification_apply(
        box_client: box.BoxClient,
        box_file_id: str,
        box_classification_name: str,
        box_classification_record: BoxClassification
):
    """
    Applies a Box file classification from an MCAS DLP policy trigger. Updates a BoxClassification object with
    the classification applys status
    """
    # Construct a SQL classification_assign object. Constructing it does not insert a record it into the database.
    # All classification_assign records are inserted in bulk at the end of the script.
    try:

        # Make the Box file classification policy set API call
        box_file = box_client.file(file_id=box_file_id).get()

        # Call the context manager rate limiter
        with box_client:
            classification = box_file.set_classification(box_classification_name)
            log.info(f"applied Box classification {classification} to file {box_file}")

        # Update the classification_assign SQL record status
        box_classification_record.APPLIED = True
    except Exception as e:
        if hasattr(e, "code") and e.status == 403:
            box_classification_record.APPLY_ERROR_FORBIDDEN = True
        else:
            box_classification_record.APPLY_ERROR_EXCEPTION_MESSAGE = str(e)

        log.info(f"failed to apply classification {box_classification_name} to file with ID {box_file_id} with {e}")


def process_box_classification_apply_batch(
        box_classification_sql_manager: BoxClassificationSQLManager,
        box_classification_tasks: list,
        box_classification_records: List[BoxClassification]
) -> None:
    """
    Runs a list of Box file classification apply tasks in a thread pool. Updates box_classification records with the
    classification apply status.
    """
    # Run the Box classification apply tasks in a thread pool
    thread.run_in_thread_pool(
        box_classification_apply,
        box_classification_tasks
    )
    # Update the the box_classification_apply SQL record's sync status
    box_classification_sql_manager.bulk_update(box_classification_records)


def retry_failed_box_classification_applys(
        box_classification_sql_manager: BoxClassificationSQLManager,
        box_client: box.BoxClient,
        box_as_user_clients: Dict[str, box.BoxClient]
) -> None:
    """
    Gets failed box_classification apply records from a SQL database, and re attempts to apply a Box file classifications
    """
    retry_batch_size = 0
    box_classification_tasks = list()
    box_classification_records = list()
    for box_classification_record in box_classification_sql_manager.failed_apply_retry_records():
        if retry_batch_size == 1000:
            process_box_classification_apply_batch(
                box_classification_sql_manager,
                box_classification_tasks,
                box_classification_records
            )
            retry_batch_size = 0
            box_classification_tasks = list()
            box_classification_records = list()

        retry_batch_size += 1
        box_classification_records.append(box_classification_record)
        box_classification_record.APPLY_ATTEMPTS += 1
        box_as_user_clients, box_as_user_client = box.get_cached_box_as_user_client(
            box_as_user_clients, box_client, box_classification_record.BOX_FILE_OWNER
        )
        box_classification_tasks.append(
            [
                box_as_user_client,
                box_classification_record.BOX_FILE_ID,
                box_classification_record.BOX_CLASSIFICATION_NAME,
                box_classification_record
            ]
        )

    if retry_batch_size:
        process_box_classification_apply_batch(
            box_classification_sql_manager,
            box_classification_tasks,
            box_classification_records
        )


@click.command()
@click.option(
    "-e", "--env", default="dev_local", help="env environment alias", type=str,
)
@config_utils.config_env
def mcas_policy_box_classification_sync(env, config):
    """
    Click CLI command to sync MCAS DLP policy trigger events with Box file classifications
    """
    # Setup a Box Platform API client
    box_client = box.configure_box_client(config)
    box_as_user_clients = dict()

    # Get MCAS API information
    mcas_subdomain = config["mcas"]["subdomain"]
    mcas_api_token = config["mcas"]["api_token"]
    mcas_rate_limiter = RateLimiter()

    # Connect to the SQL database
    sql.configure_connection(config)
    box_classification_sql_manager = BoxClassificationSQLManager(sql.connection)
    while True:
        # Get a MCAS policy from configuration
        for box_mcas_classification in config["box"]["mcas_classifications"]:
            box_classification_name = box_mcas_classification["box_name"]
            mcas_policy_id = box_mcas_classification["mcas_id"]
            mcas_files_paginate = box_mcas_classification["paginate"]
            processed_all_at = box_mcas_classification["processed_all_at"]
            now = datetime.datetime.utcnow()
            if (now - processed_all_at) > datetime.timedelta(minutes=1):
                while True:
                    # Set a list to hold Box classification apply tasks to run in a thread pool
                    box_classification_tasks = list()
                    box_classification_records = list()

                    # Poll the MCAS file endpoint
                    files_response, poll_mcas_file_again, mcas_files_paginate = mcas.poll_files(
                        mcas_subdomain, mcas_api_token, mcas_policy_id, mcas_files_paginate, mcas_rate_limiter
                    )

                    # Load the MCAS file response data to a dictionary
                    file_response_content = json.loads(files_response.content)
                    file_policy_triggers = file_response_content.get("data", [])

                    # Iterate the MCAS file endpoint response policy triggers
                    for file_policy_trigger in file_policy_triggers:
                        try:
                            # Get the policy trigger's Box file information
                            box_file_id = file_policy_trigger["boxItem"]["id"]
                            box_file_owner = file_policy_trigger["boxItem"]["owned_by"]["login"]
                            log.info(f"processing DLP policy trigger with ID {file_policy_trigger['id']} Box file ID {box_file_id} Box file owner {box_file_owner}")

                            # Insert a box_classification_apply SQL record
                            box_classification_record = box_classification_sql_manager.new_record(
                                box_file_id,
                                box_file_owner,
                                box_classification_name,
                                mcas_policy_id
                            )
                            box_classification_records.append(box_classification_record)

                            # Get a Box as user client associated to the MCAS policy trigger Box file owner
                            box_as_user_clients, box_as_user_client = box.get_cached_box_as_user_client(
                                box_as_user_clients, box_client, box_file_owner
                            )
                            if not box_as_user_client:
                                box_classification_record.APPLY_ERROR_NO_BOX_USER = True
                            else:
                                # Add the Box classification apply task arguments to a list
                                box_classification_tasks.append(
                                    [
                                        box_as_user_client,
                                        box_file_id,
                                        box_classification_name,
                                        box_classification_record
                                    ]
                                )
                        except Exception as e:
                            log.error(f"failed to process DLP policy trigger with {e}")

                    # Process the batch of Box classification apply tasks
                    process_box_classification_apply_batch(
                        box_classification_sql_manager,
                        box_classification_tasks,
                        box_classification_records
                    )

                    # Applied the configuration's MCAS classification item's pagination value
                    box_mcas_classification["paginate"] = mcas_files_paginate
                    config_utils.write_configuration(env, config)

                    if not poll_mcas_file_again:
                        box_mcas_classification["processed_all_at"] = datetime.datetime.utcnow()
                        config_utils.write_configuration(env, config)
                        break
            else:
                log.debug(f"time threshold for processing new MCAS DLP ID {mcas_policy_id} for Box classification {box_classification_name} has not elapsed")

        # Retry failed Box classification apply tasks from SQL records
        retry_failed_box_classification_applys(
            box_classification_sql_manager,
            box_client,
            box_as_user_clients
        )
