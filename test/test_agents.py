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
import asyncio
from unittest.mock import patch

from oef.agents import OEFAgent
from oef.query import Query
from .conftest import _ASYNCIO_DELAY


def test_agent_on_message_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_message is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_message_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.send_message(0, agent.public_key, b"message")

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_message in your OEFAgent class.")


def test_agent_on_cfp_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_cfp is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_cfp_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.send_cfp(0, agent.public_key, None)

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_cfp in your OEFAgent class.")


def test_agent_on_propose_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_propose is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_propose_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.send_propose(0, agent.public_key, b"propose", 0, 0)

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_propose in your OEFAgent class.")


def test_agent_on_accept_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_accept is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_accept_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.send_accept(0, agent.public_key, 0, 0)

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_accept in your OEFAgent class.")


def test_agent_on_decline_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_decline is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_decline_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.send_decline(0, agent.public_key, 0, 0)

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_decline in your OEFAgent class.")


def test_agent_on_search_result_handler_warning(oef_network_node):
    """Test that we give a warning when the handler on_search_result is not implemented."""

    with patch('logging.Logger.warning') as mock:
        agent = OEFAgent("test_agent_on_search_result_warning", "127.0.0.1", 3333)
        agent.connect()

        agent.search_agents(0, Query([]))

        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent.stop()

        mock.assert_called_with("You should implement on_search_result in your OEFAgent class.")
