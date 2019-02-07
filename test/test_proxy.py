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
from unittest.mock import patch, MagicMock

import pytest

from oef.agents import Agent, OEFAgent, LocalAgent
from oef.messages import OEFErrorOperation
from oef.proxy import OEFNetworkProxy, OEFLocalProxy, OEFConnectionError
from oef.query import Query, Gt, Constraint, Eq
from oef.schema import Description, AttributeSchema, DataModel
from test.conftest import _ASYNCIO_DELAY, NetworkOEFNode
from test.common import AgentTest, setup_test_agents

"""Parametrization to switch tests between the networked OEF Node and the local implementation of the OEF NOde."""
parametrize_node_configurations = pytest.mark.parametrize("local", [True, False], ids=["local", "networked"])


class TestSimpleMessage:

    @parametrize_node_configurations
    def test_on_message(self, local):
        """
        Test that 3 agents can send a simple message to themselves and each other and that
        the messages are properly processed and dispatched.
        """
        with setup_test_agents(3, local, prefix="on_message") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1, agent_2 = agents

            msg = b"hello"

            agent_0.send_message(0, 0, agent_0.public_key, msg)
            agent_0.send_message(0, 0, agent_1.public_key, msg)
            agent_0.send_message(0, 0, agent_2.public_key, msg)
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

            agent_1.send_message(0, 1, agent_0.public_key, msg)
            agent_1.send_message(0, 1, agent_1.public_key, msg)
            agent_1.send_message(0, 1, agent_2.public_key, msg)
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

            agent_2.send_message(0, 2, agent_0.public_key, msg)
            agent_2.send_message(0, 2, agent_1.public_key, msg)
            agent_2.send_message(0, 2, agent_2.public_key, msg)

            asyncio.ensure_future(asyncio.gather(
                    agent_0.async_run(),
                    agent_1.async_run(),
                    agent_2.async_run()))
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert 3 == len(agent_0.received_msg)
        assert 3 == len(agent_1.received_msg)
        assert 3 == len(agent_2.received_msg)

        assert (0, 0, agent_0.public_key, msg) == agent_0.received_msg[0]
        assert (0, 1, agent_1.public_key, msg) == agent_0.received_msg[1]
        assert (0, 2, agent_2.public_key, msg) == agent_0.received_msg[2]

        assert (0, 0, agent_0.public_key, msg) == agent_1.received_msg[0]
        assert (0, 1, agent_1.public_key, msg) == agent_1.received_msg[1]
        assert (0, 2, agent_2.public_key, msg) == agent_1.received_msg[2]

        assert (0, 0, agent_0.public_key, msg) == agent_2.received_msg[0]
        assert (0, 1, agent_1.public_key, msg) == agent_2.received_msg[1]
        assert (0, 2, agent_2.public_key, msg) == agent_2.received_msg[2]


class TestCFP:

    @parametrize_node_configurations
    def test_on_cfp(self, local):
        """
        Test that an agent can send a CFP to another agent, with different types of queries.
        """

        with setup_test_agents(2, local, prefix="on_cfp") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents  # type: AgentTest, AgentTest

            agent_0.send_cfp(0, 0, agent_1.public_key, 0, None)
            agent_0.send_cfp(0, 1, agent_1.public_key, 0, b"hello")
            agent_0.send_cfp(0, 2, agent_1.public_key, 0, Query([Constraint("foo", Eq(0))]))

            asyncio.ensure_future(agent_1.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        expected_message_01 = (0, 0, agent_0.public_key, 0, None)
        expected_message_02 = (0, 1, agent_0.public_key, 0, b"hello")
        expected_message_03 = (0, 2, agent_0.public_key, 0, Query([Constraint("foo", Eq(0))]))

        assert 3 == len(agent_1.received_msg)
        assert expected_message_01 == agent_1.received_msg[0]
        assert expected_message_02 == agent_1.received_msg[1]
        assert expected_message_03 == agent_1.received_msg[2]


class TestPropose:

    @parametrize_node_configurations
    def test_on_propose(self, local):
        """
        Test that an agent can send a Propose to another agent, with different types of proposals.
        """

        with setup_test_agents(2, local, prefix="on_propose") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents

            agent_0.send_propose(0, 0, agent_1.public_key, 0, b"hello")
            agent_0.send_propose(0, 0, agent_1.public_key, 0, [])
            agent_0.send_propose(0, 0, agent_1.public_key, 0, [Description({})])
            agent_0.send_propose(0, 0, agent_1.public_key, 0, [Description({}), Description({})])

            asyncio.ensure_future(agent_1.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        expected_message_01 = (0, 0, agent_0.public_key, 0, b"hello")
        expected_message_02 = (0, 0, agent_0.public_key, 0, [])
        expected_message_03 = (0, 0, agent_0.public_key, 0, [Description({})])
        expected_message_04 = (0, 0, agent_0.public_key, 0, [Description({}), Description({})])

        assert 4 == len(agent_1.received_msg)
        assert expected_message_01 == agent_1.received_msg[0]
        assert expected_message_02 == agent_1.received_msg[1]
        assert expected_message_03 == agent_1.received_msg[2]
        assert expected_message_04 == agent_1.received_msg[3]


class TestAccept:

    @parametrize_node_configurations
    def test_on_accept(self, local):
        """
        Test that an agent can send an Accept to another agent.
        """

        with setup_test_agents(2, local, prefix="on_accept") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents

            agent_0.send_accept(0, 0, agent_1.public_key, 0)

            asyncio.ensure_future(agent_1.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert 1 == len(agent_1.received_msg)
        assert (0, 0, agent_0.public_key, 0) == agent_1.received_msg[0]


class TestDecline:

    @parametrize_node_configurations
    def test_on_decline(self, local):
        """
        Test that an agent can send a Decline to another agent.
        """

        with setup_test_agents(2, local, prefix="on_decline") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents

            agent_0.send_decline(0, 0, agent_1.public_key, 0)
            asyncio.ensure_future(agent_1.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert 1 == len(agent_1.received_msg)
        assert (0, 0, agent_0.public_key, 0) == agent_1.received_msg[0]


class TestSearchServices:

    @parametrize_node_configurations
    def test_on_search_result_services(self, local):
        """
        Test that an agent can do a search for services.
        """

        with setup_test_agents(3, local, prefix="search_services") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1, agent_2 = agents

            foo_attr = AttributeSchema("foo", int, False, "A foo attribute.")
            bar_attr = AttributeSchema("bar", str, False, "A bar attribute.")

            dummy_datamodel = DataModel("dummy_datamodel", [foo_attr, bar_attr])
            desc_1 = Description({"foo": 15, "bar": "BAR"}, dummy_datamodel)
            desc_2 = Description({"foo": 5, "bar": "ABC"}, dummy_datamodel)
            agent_1.register_service(0, desc_1)
            agent_2.register_service(0, desc_2)

            agent_0.search_services(0, Query([Constraint("foo", Eq(0))], dummy_datamodel))
            agent_0.search_services(0, Query([Constraint("foo", Gt(10)), Constraint("bar", Gt("B"))], dummy_datamodel))
            agent_0.search_services(0, Query([Constraint("bar", Gt("A"))], dummy_datamodel))

            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
            agent_1.unregister_service(0, desc_1)
            agent_2.unregister_service(0, desc_2)

        expected_message_01 = (0, [])
        expected_message_02 = (0, [agent_1.public_key])
        expected_message_03 = (0, [agent_1.public_key, agent_2.public_key])

        assert 3 == len(agent_0.received_msg)
        assert expected_message_01 == agent_0.received_msg[0]
        assert expected_message_02 == agent_0.received_msg[1]
        assert expected_message_03 == agent_0.received_msg[2]


class TestSearchAgents:

    @parametrize_node_configurations
    def test_on_search_result_agents(self, local):
        """
        Test that an agent can do a search for agents.
        """

        with setup_test_agents(3, local, prefix="search_agents") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1, agent_2 = agents

            foo_attr = AttributeSchema("foo", int, False, "A foo attribute.")
            bar_attr = AttributeSchema("bar", str, False, "A bar attribute.")

            dummy_datamodel = DataModel("dummy_datamodel", [foo_attr, bar_attr])
            agent_1.register_agent(0, Description({"foo": 15, "bar": "BAR"}, dummy_datamodel))
            agent_2.register_agent(0, Description({"foo": 5, "bar": "ABC"}, dummy_datamodel))

            agent_0.search_agents(0, Query([Constraint("foo", Eq(0))], dummy_datamodel))
            agent_0.search_agents(0, Query([
                Constraint("foo", Gt(10)),
                Constraint("bar", Gt("B")),
            ], dummy_datamodel))
            agent_0.search_agents(0, Query([
                Constraint("bar", Gt("A")),
            ], dummy_datamodel))

            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))
            agent_1.unregister_agent(0)
            agent_2.unregister_agent(0)

        expected_message_01 = (0, [])
        expected_message_02 = (0, [agent_1.public_key])
        expected_message_03 = (0, [agent_1.public_key, agent_2.public_key])

        assert 3 == len(agent_0.received_msg)
        assert expected_message_01 == agent_0.received_msg[0]
        assert expected_message_02 == agent_0.received_msg[1]
        assert expected_message_03 == agent_0.received_msg[2]


class TestUnregisterAgent:

    @parametrize_node_configurations
    def test_unregister_agent(self, local):
        """
        Test that the unregistration of agents works correctly.
        """

        with setup_test_agents(2, local, prefix="unregister_agent") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents

            dummy_datamodel = DataModel("dummy_datamodel", [AttributeSchema("foo", int, False)])
            agent_1.register_agent(0, Description({}, dummy_datamodel))
            agent_1.unregister_agent(0)

            agent_0.search_agents(0, Query([Constraint("foo", Eq(0))], dummy_datamodel))
            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert 1 == len(agent_0.received_msg)
        assert (0, []) == agent_0.received_msg[0]


class TestUnregisterService:

    @parametrize_node_configurations
    def test_unregister_service(self, local):
        """
        Test that the unregistration of services works correctly.
        """

        with setup_test_agents(2, local, prefix="unregister_service") as agents:

            for a in agents:
                a.connect()

            agent_0, agent_1 = agents

            dummy_datamodel = DataModel("dummy_datamodel", [AttributeSchema("foo", int, False)])
            dummy_service_description = Description({}, dummy_datamodel)
            agent_1.register_service(0, dummy_service_description)
            agent_1.unregister_service(0, dummy_service_description)

            agent_0.search_services(0, Query([Constraint("foo", Eq(0))], dummy_datamodel))
            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        assert 1 == len(agent_0.received_msg)
        assert (0, []) == agent_0.received_msg[0]


class TestOEFError:

    def test_oef_error_when_failing_in_unregistering_service(self):
        """Test that we receive an OEF Error message when we try to unregister a non existing service."""

        with setup_test_agents(1, False, prefix="oef_error_unregister_description") as agents:

            for a in agents:
                a.connect()

            agent_0 = agents[0]  # type: AgentTest
            agent_0.on_oef_error = MagicMock()

            agent_0.unregister_service(0, Description({"foo": 1}))

            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        agent_0.on_oef_error.assert_called_with(0, OEFErrorOperation.UNREGISTER_SERVICE)


class TestDialogueError:

    def test_dialogue_error_when_destination_is_not_connected(self):
        """Test that we receive an ``DialogueError`` message when we try to send a message to an unconnected agent."""

        with setup_test_agents(1, False, prefix="dialogue_error_unconnected_destination") as agents:

            for a in agents:
                a.connect()

            agent_0 = agents[0]  # type: AgentTest
            agent_0.on_dialogue_error = MagicMock()

            # send a message to an unconnected agent
            agent_0.send_message(0, 0, "unconnected_agent", b"dummy_message")

            asyncio.ensure_future(agent_0.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

        agent_0.on_dialogue_error.assert_called_with(0, 0, "unconnected_agent")


class TestConnect:

    def test_connection_error_on_send(self):
        """Test that a OEFConnectionError is raised when we try to send a message before
        the connection has been established."""
        with NetworkOEFNode():
            with pytest.raises(OEFConnectionError, match="Connection not established yet."):
                proxy = OEFNetworkProxy("test_oef_connection_error_when_send", "127.0.0.1", 3333)
                agent = Agent(proxy)
                agent.send_message(0, 0, proxy.public_key, b"message")

    def test_connection_error_on_receive(self):
        """Test that a OEFConnectionError is raised when we try to send a message before
        the connection has been established."""
        with NetworkOEFNode():
            with pytest.raises(OEFConnectionError, match="Connection not established yet."):
                proxy = OEFNetworkProxy("test_oef_connection_error_when_receive", "127.0.0.1", 3333)
                agent = Agent(proxy)
                agent.run()

    def test_that_two_connect_attempts_work_correctly(self):
        """Test that two call to the :func:'~agents.Agent.connect()' method work correctly.
        Use the local implementation of the OEF."""
        with NetworkOEFNode():
            agent_1 = OEFAgent("two_connect_attempt", "127.0.0.1", 3333)
            first_status = agent_1.connect()
            second_status = agent_1.connect()

        assert first_status
        assert second_status

    def test_that_two_connect_attempts_work_correctly_local_node(self):
        """Test that two call to the :func:'~agents.Agent.connect()' method work correctly."""
        with OEFLocalProxy.LocalNode() as local_node:
            agent_1 = LocalAgent("two_connect_attempt", local_node)
            first_status = agent_1.connect()
            second_status = agent_1.connect()

        assert first_status
        assert second_status

    def test_connection_error_public_key_already_in_use(self):
        """Test that a OEFConnectionError is raised when we try to connect two agents with the same public key."""
        with pytest.raises(OEFConnectionError, match="Public key already in use."):
            with NetworkOEFNode():
                agent_1 = OEFAgent("the_same_public_key", "127.0.0.1", 3333)
                agent_2 = OEFAgent(agent_1.public_key, "127.0.0.1", 3333)
                agent_1.connect()
                agent_2.connect()

    def test_connection_error_public_key_already_in_use_local_node(self):
        """Test that a OEFConnectionError is raised when we try to connect two agents with the same public key.
        Use the local implementation of the OEF."""
        with pytest.raises(OEFConnectionError, match="Public key already in use."):
            with OEFLocalProxy.LocalNode() as local_node:
                agent_1 = LocalAgent("the_same_public_key", local_node)
                agent_2 = LocalAgent(agent_1.public_key, local_node)
                agent_1.connect()
                agent_2.connect()


class TestDisconnect:

    def test_disconnect(self):
        """Test that the disconnect method works correctly."""

        with NetworkOEFNode():
            agent_1 = OEFAgent("disconnect", "127.0.0.1", 3333)
            assert not agent_1._oef_proxy.is_connected()
            agent_1.connect()
            assert agent_1._oef_proxy.is_connected()
            agent_1.disconnect()
            assert not agent_1._oef_proxy.is_connected()

    def test_disconnect_local(self):
        """Test that the disconnect method works correctly."""

        with OEFLocalProxy.LocalNode() as local_node:
            agent_1 = LocalAgent("disconnect", local_node)
            assert not agent_1._oef_proxy.is_connected()
            agent_1.connect()
            assert agent_1._oef_proxy.is_connected()
            agent_1.disconnect()
            assert not agent_1._oef_proxy.is_connected()


class TestMisc:

    def test_more_than_once_async_run_call(self):
        """Test that when we call async_run more than once we get a warning message."""
        with NetworkOEFNode():
            with patch('logging.Logger.warning') as mock:
                proxy = OEFNetworkProxy("test_more_than_one_async_run_call", "127.0.0.1", 3333)
                agent = Agent(proxy)
                agent.connect()

                asyncio.ensure_future(agent.async_run())
                asyncio.ensure_future(agent.async_run())
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

                mock.assert_called_with("Agent {} already scheduled for running.".format(agent.public_key))

    def test_send_more_than_64_kilobytes(self):
        """Test that we can send more than 64KB messages."""
        with NetworkOEFNode():
            proxy = OEFNetworkProxy("test_send_more_than_64_kilobytes", "127.0.0.1", 3333)
            agent = AgentTest(proxy)

            expected_msg_id = 0
            expected_dialogue_id = 0
            expected_content = b"a"*2**16
            expected_origin = agent.public_key

            agent.connect()
            agent.send_message(expected_msg_id, expected_dialogue_id, agent.public_key, expected_content)
            asyncio.ensure_future(agent.async_run())
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(_ASYNCIO_DELAY))

            agent.stop()

        actual_msg_id, actual_dialogue_id, actual_origin, actual_content = agent.received_msg[0]

        # assert that we received only one message
        assert 1 == len(agent.received_msg)

        # assert that the message contains what we've sent.
        assert expected_msg_id == actual_msg_id
        assert expected_dialogue_id == actual_dialogue_id
        assert expected_origin == actual_origin
        assert expected_content == actual_content
