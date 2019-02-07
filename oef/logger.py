# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------


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
