# Copyright (C) Fetch.ai 2018 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import logging
from typing import List

_DEFAULT_LOG_FORMAT = '[%(asctime)s][%(name)s][%(funcName)s][%(levelname)s] %(message)s'


def set_logger(name, level=logging.INFO, handlers: List[logging.Handler] = None):
    """
    Utility to set up a logger, for a given module.

    >>> logger = set_logger("oef", logging.DEBUG)

    :param name: the name of the module to audit. This can be the name of the package (e.g. ``"oef"``)
           | or any child module (e.g. ``"oef.agents"``).
    :param level: the logging level
    :param handlers: a list of logging handlers. If None, then a default StreamHandler is provided,
           | printing to standard error.
    :return: the logger.
    """

    # Make the logger for the oef package.
    # This configuration will propagate to the child modules.
    logger = logging.getLogger(name)

    # Set the level.
    logger.setLevel(level)

    # Make the handler and attach it.
    if handlers is None:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
        handler.setFormatter(formatter)
        handlers = [handler]

    # Make the handler the unique handler for the logger.
    logger.handlers = handlers

    return logger
