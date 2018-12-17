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

from logging import Logger, CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET, StreamHandler, NullHandler

import pytest
from oef.logger import set_logger


@pytest.mark.parametrize("logging_level", [CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET])
@pytest.mark.parametrize("handlers", [[StreamHandler()], [NullHandler()], None])
def test_set_logger(logging_level, handlers):
    """Test that the ``set_logger`` utility function behaves as expected."""
    logger = set_logger("oef", level=logging_level, handlers=handlers)

    assert isinstance(logger, Logger)
    assert logging_level == logger.level

    if handlers:
        assert logger.handlers == handlers
    else:
        assert len(logger.handlers) == 1
        assert type(logger.handlers[0]) == StreamHandler
