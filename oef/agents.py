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


"""

oef.agents
~~~~~~~~~~

This module contains the base class for implementing agents.

"""
import asyncio
import logging
from abc import ABC
from typing import Optional, List

from oef import agent_pb2
from oef.core import OEFProxy, AgentInterface
from oef.proxy import OEFNetworkProxy, PROPOSE_TYPES, CFP_TYPES, OEFLocalProxy, OEFConnectionError
from oef.query import Query
from oef.schema import Description

logger = logging.getLogger(__name__)


def _warning_not_implemented_method(method_name: str) -> None:
    """
    Raise a warning if a method has not been implemented.

    :param method_name: the method name to report in the warning
    :return: ``None``
    """
    logger.warning("You should implement {} in your OEFAgent class.".format(method_name))


class Agent(AgentInterface, ABC):
    """
    The base class for OEF Agents.

    Extend this class to implement the callback methods defined in
    :class:`~oef.core.DialogueInterface` and :class:`~oef.core.ConnectionInterface`.

    In this way you can program the behaviour of the agent when it's running.
    """

    @property
    def public_key(self) -> str:
        """
        The public key that identifies the agent in the OEF.

        :return: the public key.
        """
        return self.oef_proxy.public_key

    def __init__(self, oef_proxy: OEFProxy):
        """
        Initialize the OEF Agent.

        :param oef_proxy: the proxy for an OEF Node.
        """

        self.oef_proxy = oef_proxy
        self._task = None
        self._loop = asyncio.get_event_loop()

    def run(self) -> None:
        """
        Run the agent synchronously. That is, until :func:`~oef.agents.Agent.stop` is not called.

        :return: ``None``
        """
        self._loop.run_until_complete(self.async_run())

    async def async_run(self) -> None:
        """
        Run the agent asynchronously.

        :return: ``None``
        """
        if self._task:
            logger.warning("Agent {} already scheduled for running.".format(self.public_key))
            return
        self._task = asyncio.ensure_future(self.oef_proxy.loop(self))
        await self._task

    def stop(self) -> None:
        """
        Stop the agent. Specifically, if :func:`~oef.agents.Agent.run` or :func:`~oef.agents.Agent.async_run`
        have been called, then this method will cancel the previously instantiated task.
        The task that manages the agent-loop is hence scheduled for cancellation.

        :return: ``None``
        """
        if self._task:
            self._task.cancel()
            self._task = None
            self.oef_proxy.stop()

    def connect(self) -> bool:
        """
        Connect to the OEF Node.

        :return: True if the connection has been established successfully, False otherwise.
        """
        return self._loop.run_until_complete(self.async_connect())

    async def async_connect(self) -> bool:
        """
        The asynchronous counterpart of :func:`~oef.agents.Agent.connect`.

        :return: True if the connection has been established successfully, False otherwise.
        """
        logger.debug("{}: Connecting...".format(self.public_key))
        status = await self.oef_proxy.connect()
        if status:
            logger.debug("{}: Connection established.".format(self.public_key))
        else:
            raise OEFConnectionError("Public key already in use.")
        return status

    def register_agent(self, agent_description: Description) -> None:
        self.oef_proxy.register_agent(agent_description)

    def unregister_agent(self) -> None:
        self.oef_proxy.unregister_agent()

    def register_service(self, service_description: Description) -> None:
        self.oef_proxy.register_service(service_description)

    def unregister_service(self, service_description: Description) -> None:
        self.oef_proxy.unregister_service(service_description)

    def search_agents(self, search_id: int, query: Query) -> None:
        self.oef_proxy.search_agents(search_id, query)

    def search_services(self, search_id: int, query: Query) -> None:
        self.oef_proxy.search_services(search_id, query)

    def send_message(self, dialogue_id: int,
                     destination: str,
                     msg: bytes) -> None:
        logger.debug("Agent {}: dialogue_id={}, destination={}, msg={}"
                     .format(self.public_key,
                             dialogue_id,
                             destination,
                             msg))
        self.oef_proxy.send_message(dialogue_id, destination, msg)

    def send_cfp(self, dialogue_id: int,
                 destination: str,
                 query: CFP_TYPES,
                 msg_id: Optional[int] = 1,
                 target: Optional[int] = 0) -> None:
        logger.debug("Agent {}: dialogue_id={}, destination={}, query={}, msg_id={}, target={}"
                     .format(self.public_key,
                             dialogue_id,
                             destination,
                             query,
                             msg_id,
                             target))
        self.oef_proxy.send_cfp(dialogue_id, destination, query, msg_id, target)

    def send_propose(self, dialogue_id: int,
                     destination: str,
                     proposals: PROPOSE_TYPES,
                     msg_id: int,
                     target: Optional[int] = None) -> None:
        logger.debug("Agent {}: dialogue_id={}, destination={}, proposals={}, msg_id={}, target={}"
                     .format(self.public_key,
                             dialogue_id,
                             destination,
                             proposals,
                             msg_id,
                             target))
        self.oef_proxy.send_propose(dialogue_id, destination, proposals, msg_id, target)

    def send_accept(self, dialogue_id: int,
                    destination: str,
                    msg_id: int,
                    target: Optional[int] = None) -> None:
        logger.debug("Agent {}: dialogue_id={}, destination={}, msg_id={}, target={}"
                     .format(self.public_key,
                             dialogue_id,
                             destination,
                             msg_id,
                             target))
        self.oef_proxy.send_accept(dialogue_id, destination, msg_id, target)

    def send_decline(self, dialogue_id: int,
                     destination: str,
                     msg_id: int,
                     target: Optional[int] = None) -> None:
        logger.debug("Agent {}: dialogue_id={}, destination={}, msg_id={}, target={}"
                     .format(self.public_key,
                             dialogue_id,
                             destination,
                             msg_id,
                             target))
        self.oef_proxy.send_decline(dialogue_id, destination, msg_id, target)

    def on_message(self, origin: str,
                   dialogue_id: int,
                   content: bytes):
        logger.debug("on_message: {}, {}, {}".format(origin, dialogue_id, content))
        _warning_not_implemented_method(self.on_message.__name__)

    def on_cfp(self, origin: str,
               dialogue_id: int,
               msg_id: int,
               target: int,
               query: CFP_TYPES):
        logger.debug("on_cfp: {}, {}, {}, {}, {}".format(origin, dialogue_id, msg_id, target, query))
        _warning_not_implemented_method(self.on_cfp.__name__)

    def on_accept(self, origin: str,
                  dialogue_id: int,
                  msg_id: int,
                  target: int, ):
        logger.debug("on_accept: {}, {}, {}, {}".format(origin, dialogue_id, msg_id, target))
        _warning_not_implemented_method(self.on_accept.__name__)

    def on_decline(self, origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int, ):
        logger.debug("on_decline: {}, {}, {}, {}".format(origin, dialogue_id, msg_id, target))
        _warning_not_implemented_method(self.on_decline.__name__)

    def on_propose(self, origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int,
                   proposal: PROPOSE_TYPES):
        logger.debug("on_propose: {}, {}, {}, {}, {}".format(origin, dialogue_id, msg_id, target, proposal))
        _warning_not_implemented_method(self.on_propose.__name__)

    def on_error(self, operation: agent_pb2.Server.AgentMessage.Error.Operation,
                 dialogue_id: int,
                 message_id: int):
        logger.debug("on_error: {}, {}, {}".format(operation, dialogue_id, message_id))
        _warning_not_implemented_method(self.on_error.__name__)

    def on_search_result(self, search_id: int, agents: List[str]):
        logger.debug("on_search_result: {}, {}".format(search_id, agents))
        _warning_not_implemented_method(self.on_search_result.__name__)


class OEFAgent(Agent):
    """
    Agent that interacts with an OEFNode on the network.

    It provides a nicer constructor that does not require to instantiate :class:`~oef.proxy.OEFLocalProxy` explicitly.
    """

    def __init__(self, public_key: str, oef_addr: str, oef_port: int = 3333) -> None:
        """
        Initialize an OEF network agent.

        :param public_key: the public key (identifier) of the agent
        :param oef_addr: the IP address of the OEF Node.
        :param oef_port: the port for the connection.
        """
        self._oef_addr = oef_addr
        self._oef_port = oef_port
        super().__init__(OEFNetworkProxy(public_key, str(self._oef_addr), self._oef_port))


class LocalAgent(Agent):
    """
    Agent that interacts with a local implementation of an OEF Node.

    It provides a nicer constructor that does not require to instantiate :class:`~oef.proxy.OEFLocalProxy` explicitly.

    Notice: other agents need to be constructed with the same :class:`~oef.proxy.OEFLocalProxy.LocalNode` instance.
    """

    def __init__(self, public_key: str, local_node: OEFLocalProxy.LocalNode):
        """
        Initialize an OEF local agent.

        :param public_key: the public key (identifier) of the agent.
        :param local_node: an instance of the local implementation of the OEF Node.
        """
        super().__init__(OEFLocalProxy(public_key, local_node))
