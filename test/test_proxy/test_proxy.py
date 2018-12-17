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
import contextlib
from typing import List, Tuple
from unittest.mock import patch

import pytest

from oef.agents import Agent, OEFAgent, LocalAgent
from oef.schema import Description, DataModel

from oef.query import Query

from oef.proxy import OEFLocalProxy, OEFNetworkProxy, OEFConnectionError
from test.conftest import _ASYNCIO_DELAY
from test.test_proxy.agent_test import AgentTest


@contextlib.contextmanager
def setup_test_agents(n: int, local: bool, prefix: str="") -> List[AgentTest]:
    agents, local_node = _init_context(n, local, prefix)
    try:
        yield agents
    except Exception:
        raise
    finally:
        if local_node:
            local_node.stop()
        _stop_agents(agents)


def _init_context(n: int, local: bool, prefix: str= "") -> Tuple[List[AgentTest], OEFLocalProxy.LocalNode]:
    """
    Initialize a context for testing agent communications.

    :param n: the number of agents.
    :param local: whether the context is local or networked.
    :param prefix: the prefix to add at the beginning of every agent public key.
    :return:
    """
    public_key_prefix = prefix + "-" if prefix else ""
    local_node = None
    if local:
        local_node = OEFLocalProxy.LocalNode()
        proxies = [OEFLocalProxy("{}agent-{}".format(public_key_prefix, i), local_node) for i in range(n)]
        asyncio.ensure_future(local_node.run())
    else:
        proxies = [OEFNetworkProxy("{}agent-{}".format(public_key_prefix, i), "127.0.0.1", 3333) for i in range(n)]

    agents = [AgentTest(proxy) for proxy in proxies]
    for a in agents:
        a.connect()

    return agents, local_node


def _stop_agents(agents):
    for a in agents:
        a.stop()

    for t in asyncio.Task.all_tasks():
        asyncio.get_event_loop().run_until_complete(t)


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_message(oef_network_node, is_local):
    """
    Test that 3 agents can send a simple message to themselves and each other and that
    the messages are properly processed and dispatched.
    """
    with setup_test_agents(3, is_local, prefix="on_message") as agents:
        agent_0, agent_1, agent_2 = agents

        msg = b"hello"

        agent_0.send_message(0, agent_0.public_key, msg)
        agent_0.send_message(0, agent_1.public_key, msg)
        agent_0.send_message(0, agent_2.public_key, msg)

        agent_1.send_message(0, agent_0.public_key, msg)
        agent_1.send_message(0, agent_1.public_key, msg)
        agent_1.send_message(0, agent_2.public_key, msg)

        agent_2.send_message(0, agent_0.public_key, msg)
        agent_2.send_message(0, agent_1.public_key, msg)
        agent_2.send_message(0, agent_2.public_key, msg)

        asyncio.ensure_future(asyncio.gather(
                agent_0.async_run(),
                agent_1.async_run(),
                agent_2.async_run()))
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_0.received_msg) == 3
        assert len(agent_1.received_msg) == 3
        assert len(agent_2.received_msg) == 3

        assert agent_0.received_msg[0] == (agent_0.public_key, 0, msg)
        assert agent_0.received_msg[1] == (agent_1.public_key, 0, msg)
        assert agent_0.received_msg[2] == (agent_2.public_key, 0, msg)
        assert agent_1.received_msg[0] == (agent_0.public_key, 0, msg)
        assert agent_1.received_msg[1] == (agent_1.public_key, 0, msg)
        assert agent_1.received_msg[2] == (agent_2.public_key, 0, msg)
        assert agent_2.received_msg[0] == (agent_0.public_key, 0, msg)
        assert agent_2.received_msg[1] == (agent_1.public_key, 0, msg)
        assert agent_2.received_msg[2] == (agent_2.public_key, 0, msg)


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_cfp(oef_network_node, is_local):
    """
    Test that an agent can send a CFP to another agent, with different types of queries.
    """

    with setup_test_agents(2, is_local, prefix="on_cfp") as agents:
        agent_0, agent_1 = agents

        agent_0.send_cfp(0, agent_1.public_key, None, 1, 0)
        agent_0.send_cfp(0, agent_1.public_key, b"hello", 1, 0)
        agent_0.send_cfp(0, agent_1.public_key, Query([]), 1, 0)

        asyncio.ensure_future(agent_1.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_1.received_msg) == 3
        assert agent_1.received_msg[0] == (agent_0.public_key, 0, 1, 0, None)
        assert agent_1.received_msg[1] == (agent_0.public_key, 0, 1, 0, b"hello")
        assert agent_1.received_msg[2] == (agent_0.public_key, 0, 1, 0, Query([]))


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_propose(oef_network_node, is_local):
    """
    Test that an agent can send a Propose to another agent, with different types of proposals.
    """

    with setup_test_agents(2, is_local, prefix="on_propose") as agents:

        agent_0, agent_1 = agents

        agent_0.send_propose(0, agent_1.public_key, b"hello", 1, 0)
        agent_0.send_propose(0, agent_1.public_key, [], 1, 0)
        agent_0.send_propose(0, agent_1.public_key, [Description({})], 1, 0)
        agent_0.send_propose(0, agent_1.public_key, [Description({}), Description({})], 1, 0)

        asyncio.ensure_future(agent_1.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_1.received_msg) == 4
        assert agent_1.received_msg[0] == (agent_0.public_key, 0, 1, 0, b"hello")
        assert agent_1.received_msg[1] == (agent_0.public_key, 0, 1, 0, [])
        assert agent_1.received_msg[2] == (agent_0.public_key, 0, 1, 0, [Description({})])
        assert agent_1.received_msg[3] == (agent_0.public_key, 0, 1, 0, [Description({}), Description({})])


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_accept(oef_network_node, is_local):
    """
    Test that an agent can send an Accept to another agent, with different types of proposals.
    """

    with setup_test_agents(2, is_local, prefix="on_accept") as agents:
        agent_0, agent_1 = agents

        agent_0.send_accept(0, agent_1.public_key, 1, 0)

        asyncio.ensure_future(agent_1.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_1.received_msg) == 1
        assert agent_1.received_msg[0] == (agent_0.public_key, 0, 1, 0)


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_decline(oef_network_node, is_local):
    """
    Test that an agent can send a Decline to another agent, with different types of proposals.
    """

    with setup_test_agents(2, is_local, prefix="on_decline") as agents:
        agent_0, agent_1 = agents

        agent_0.send_decline(0, agent_1.public_key, 1, 0)
        asyncio.ensure_future(agent_1.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_1.received_msg) == 1
        assert agent_1.received_msg[0] == (agent_0.public_key, 0, 1, 0)


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_search_result_services(oef_network_node, is_local):
    """
    Test that an agent can do a search for services.
    """

    with setup_test_agents(3, is_local, prefix="search_services") as agents:

        agent_0, agent_1, agent_2 = agents

        dummy_datamodel = DataModel("dummy_datamodel", [])
        agent_1.register_service(Description({}, dummy_datamodel))
        agent_2.register_service(Description({}, dummy_datamodel))

        agent_0.search_services(0, Query([], dummy_datamodel))
        asyncio.ensure_future(agent_0.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent_1.unregister_service(Description({}, dummy_datamodel))
        agent_2.unregister_service(Description({}, dummy_datamodel))

        assert len(agent_0.received_msg) == 1
        assert agent_0.received_msg[0] == (0, [agent_1.public_key, agent_2.public_key])


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_on_search_result_agents(oef_network_node, is_local):
    """
    Test that an agent can do a search for agents.
    """

    with setup_test_agents(3, is_local, prefix="search_agents") as agents:

        agent_0, agent_1, agent_2 = agents

        dummy_datamodel = DataModel("dummy_datamodel", [])
        agent_1.register_agent(Description({}, dummy_datamodel))
        agent_2.register_agent(Description({}, dummy_datamodel))

        agent_0.search_agents(0, Query([], dummy_datamodel))
        asyncio.ensure_future(agent_0.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
        agent_1.unregister_agent()
        agent_2.unregister_agent()

        assert len(agent_0.received_msg) == 1
        assert agent_0.received_msg[0] == (0, [agent_1.public_key, agent_2.public_key])


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_unregister_agent(oef_network_node, is_local):
    """
    Test that the unregistration of agents works correctly.
    """

    with setup_test_agents(2, is_local, prefix="unregister_agent") as agents:

        agent_0, agent_1 = agents

        dummy_datamodel = DataModel("dummy_datamodel", [])
        agent_1.register_agent(Description({}, dummy_datamodel))
        agent_1.unregister_agent()

        agent_0.search_agents(0, Query([], dummy_datamodel))
        asyncio.ensure_future(agent_0.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_0.received_msg) == 1
        assert agent_0.received_msg[0] == (0, [])


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "networked"])
def test_unregister_service(oef_network_node, is_local):
    """
    Test that the unregistration of services works correctly.
    """

    with setup_test_agents(2, is_local, prefix="unregister_service") as agents:
        agent_0, agent_1 = agents

        dummy_datamodel = DataModel("dummy_datamodel", [])
        dummy_service_description = Description({}, dummy_datamodel)
        agent_1.register_service(dummy_service_description)
        agent_1.unregister_service(dummy_service_description)

        agent_0.search_services(0, Query([], dummy_datamodel))
        asyncio.ensure_future(agent_0.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert len(agent_0.received_msg) == 1
        assert agent_0.received_msg[0] == (0, [])


def test_connection_error_on_send(oef_network_node):
    """Test that a OEFConnectionError is raised when we try to send a message before
    the connection has been established."""
    with pytest.raises(OEFConnectionError, match="Connection not established yet."):
        proxy = OEFNetworkProxy("test_oef_connection_error_when_send", "127.0.0.1", 3333)
        agent = Agent(proxy)
        agent.send_message(0, proxy.public_key, b"message")


def test_connection_error_on_receive(oef_network_node):
    """Test that a OEFConnectionError is raised when we try to send a message before
    the connection has been established."""
    with pytest.raises(OEFConnectionError, match="Connection not established yet."):
        proxy = OEFNetworkProxy("test_oef_connection_error_when_receive", "127.0.0.1", 3333)
        agent = Agent(proxy)
        agent.run()


def test_connection_error_public_key_already_in_use(oef_network_node):
    """Test that a OEFConnectionError is raised when we try to connect two agents with the same public key."""
    with pytest.raises(OEFConnectionError, match="Public key already in use."):
        agent_1 = OEFAgent("the_same_public_key", "127.0.0.1", 3333)
        agent_2 = OEFAgent(agent_1.public_key, "127.0.0.1", 3333)
        agent_1.connect()
        agent_2.connect()


def test_connection_error_public_key_already_in_use_local_node(oef_network_node):
    """Test that a OEFConnectionError is raised when we try to connect two agents with the same public key.
    Local version."""
    with pytest.raises(OEFConnectionError, match="Public key already in use."):
        local_node = OEFLocalProxy.LocalNode()
        agent_1 = LocalAgent("the_same_public_key", local_node)
        agent_2 = LocalAgent(agent_1.public_key, local_node)
        agent_1.connect()
        agent_2.connect()


def test_more_than_one_connect_call(oef_network_node):
    proxy = OEFNetworkProxy("test_more_than_one_connect_call", "127.0.0.1", 3333)
    agent = Agent(proxy)
    agent.connect()
    assert agent.connect()


def test_more_than_one_async_run_call(oef_network_node):
    with patch('logging.Logger.warning') as mock:
        proxy = OEFNetworkProxy("test_more_than_one_async_run_call", "127.0.0.1", 3333)
        agent = Agent(proxy)
        agent.connect()

        asyncio.ensure_future(agent.async_run())
        asyncio.ensure_future(agent.async_run())
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        mock.assert_called_with("Agent {} already scheduled for running.".format(agent.public_key))
