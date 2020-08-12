"""
Configuration utilities
"""

import logging.config
import logging
import os
import functools
from typing import Callable

import yaml


log = logging.getLogger(__name__)


def configure_logging(configuration: dict) -> None:
    """
    Writes log files and configures logging from a configuration dictionary
    """
    log_dict_config = configuration["log"]
    for handler_alias, handler_config in log_dict_config["handlers"].items():
        if "filename" in handler_config.keys():
            log_file_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "logs",
                handler_config["filename"],
            )
            if not os.path.exists(log_file_path):
                with open(log_file_path, "w"):
                    pass

            handler_config["filename"] = log_file_path

    logging.config.dictConfig(log_dict_config)
    log.debug(f"configured logging")


def load_configuration(env_alias: str) -> dict:
    """
    Loads a YAML configuration file from its environment name alias
    """
    with open(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "configuration",
            f"{env_alias}.yml",
        ),
        "r",
    ) as fh:
        config = yaml.load(fh, Loader=yaml.FullLoader)
        log.debug("loaded configuration")
        return config


def write_configuration(env_alias: str, config_dict: dict) -> None:
    """
    Writes to a YAML configuration file from its environment name alias
    """
    with open(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "configuration",
            f"{env_alias}.yml",
        ),
        "w",
    ) as fh:
        yaml.dump(config_dict, fh, default_flow_style=False)
        log.debug("wrote configuration")


def config_env(func: Callable) -> Callable:
    """
    Decorator to add a YAML configuration loaded into a diction as a key word argument to the decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        env_alias = kwargs.get("env")
        if not env_alias:
            raise TypeError("Missing 'env' kwargs")

        config = load_configuration(env_alias)
        configure_logging(config)
        log.info(f"Running {func.__name__} CLI")
        kwargs["config"] = config

        return func(*args, **kwargs)

    return wrapper
