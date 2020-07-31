"""
Microsoft Cloud App Security API utilities
"""

import json
import logging
from typing import Optional, Tuple

import requests

from src import http_utils


log = logging.getLogger(__name__)


def poll_files(
        subdomain: str,
        api_token: str,
        mcas_policy_id: str,
        paginate: int,
        rate_limiter: http_utils.RateLimiter,
) -> Tuple[requests.Response, bool, int]:
    """
    Polls the MCAS files endpoint while enforcing rate limits
    """
    poll_mcas_file_again = False
    try:
        with rate_limiter:
            mcas_post_files_body = {"filters": {
                "fileType": {"neq": [6]},
                "policy": {"cabinetmatchedrulesequals": [mcas_policy_id]}
            }}
            response = post_files(
                subdomain, api_token, paginate, mcas_post_files_body,
            )
            log.debug(f"got MCAS files response {response}")
            mcas_post_files_resp_json = json.loads(response.content)
            if mcas_post_files_resp_json.get("hasNext"):
                poll_mcas_file_again = True
                paginate += 1

    except Exception as e:
        log.error(f"{e}")

    return response, poll_mcas_file_again, paginate


def post_files(
        subdomain: str,
        api_token: str,
        paginate: int,
        json_body: Optional[dict] = None
) -> requests.Response:
    """
    POSTs to the MCAS files endpoint
    """
    return requests.post(
        f"https://{subdomain}.portal.cloudappsecurity.com/api/v1/files/?skip={paginate}",
        headers={"Authorization": f"Token {api_token}"},
        json=json_body,
    )
