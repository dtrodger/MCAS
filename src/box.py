"""
Box Platform utilities
"""

from __future__ import annotations
import logging
from typing import Tuple, Dict

import boxsdk

from src import http_utils


log = logging.getLogger(__name__)


def configure_box_auth(config: dict) -> boxsdk.JWTAuth:
    """
    Instantiates a boxsdk.JWTAuth object from a configuration dictionary and authenticates it against
    Box Platform's authentication service
    """
    box_auth = boxsdk.JWTAuth.from_settings_dictionary(config["box"]["jwt"])
    box_auth.authenticate_instance()

    return box_auth


def configure_box_client(config: dict) -> BoxClient:
    """
    Configures a Box Platform REST client from a configuration dictionary
    """
    box_auth = configure_box_auth(config)
    box_client = BoxClient(box_auth)

    return box_client


def as_user_client(client: boxsdk.Client, user_email: str) -> BoxClient:
    """
    Returns a Box Platform as-user REST client
    """
    try:
        user = client.users(filter_term=user_email, limit=1).next()

        return client.as_user(user)
    except StopIteration:
        log.info(f"no Box user found with email {user_email}")


def get_cached_box_as_user_client(
        box_as_user_clients: Dict[str, BoxClient],
        box_client: BoxClient,
        box_file_owner: str
) -> Tuple[Dict[str, BoxClient], BoxClient]:
    """
    Checks for a cached Box Platform as-user REST client. Gets and cached a Box Platform as-user REST client if none is
    found
    """
    box_as_user_client = box_as_user_clients.get(box_file_owner)
    if not box_as_user_client:
        box_client = BoxClient(box_client._oauth)
        box_as_user_client = as_user_client(
            box_client, box_file_owner
        )
        if box_as_user_client:
            box_as_user_clients[box_file_owner] = box_as_user_client
            log.info(f"cached Box as-user client for user {box_file_owner}")
        else:
            log.info(f"no Box as user client cached for file owner {box_file_owner}")
    else:
        log.info(f"got cached Box as-user client for user {box_file_owner}")

    return box_as_user_clients, box_as_user_client


class BoxClient(boxsdk.Client):
    """
    boxsdk.Client subclass implementing rate limiting
    """

    def __init__(self, oauth, session=None, rate_limit=12) -> BoxClient:
        super().__init__(oauth, session)
        self._rate_limiter = http_utils.RateLimiter(rate_limit)

    def __enter__(self) -> None:
        """
        Context manager enter that blocks until a rate limited call can be made
        """
        with self._rate_limiter:
            return

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit
        """
        pass