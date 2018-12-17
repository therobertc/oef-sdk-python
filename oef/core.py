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

oef.core
~~~~~~~~

The core module that contains the main abstraction of the SDK.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from oef import agent_pb2 as agent_pb2
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.query import Query
from oef.schema import Description

logger = logging.getLogger(__name__)


class OEFCoreInterface(ABC):
    """Methods to interact with an OEF node."""

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the OEF Node

        :return: True if the connection has been established, False otherwise.
        """

    @abstractmethod
    def register_agent(self, agent_description: Description) -> None:
        """
        Adds a description of an agent to the OEF so that it can be understood/ queried by
        other agents in the OEF.

        :param agent_description: description of the agent to add
        :return: ``None``
        """

    @abstractmethod
    def register_service(self, service_description: Description) -> None:
        """
        Adds a description of the respective service so that it can be understood/queried by
        other agents in the OEF.

        :param service_description: description of the services to add
        :return: ``None``
        """

    @abstractmethod
    def search_agents(self, search_id: int, query: Query) -> None:
        """
        Search for other agents it is interested in communicating with. This can
        be useful when an agent wishes to directly proposition the provision of a service that it
        thinks another agent may wish to be able to offer it. All matching agents are returned
        (potentially including ourselves).

        :param search_id: the identifier of the search to whom the result is answering.
        :param query: specifications of the constraints on the agents that are matched
        :return: ``None``.
        """

    @abstractmethod
    def search_services(self, search_id: int, query: Query) -> None:
        """
        Search for a particular service. This allows constrained search of all
        services that have been registered with the OEF. All matching services will be returned
        (potentially including services offered by ourselves).

        :param search_id: the identifier of the search to whom the result is answering.
        :param query: the constraint on the matching services
        :return: ``None``.
        """

    @abstractmethod
    def unregister_agent(self) -> None:
        """
        Remove the description of an agent from the OEF. This agent will no longer be queryable
        by other agents in the OEF. A conversation handler must be provided that allows the agent
        to receive and manage conversations from other agents wishing to communicate with it.

        :return: ``None``
        """

    @abstractmethod
    def unregister_service(self, service_description: Description) -> None:
        """
        Add a description of the respective service so that it can be understood/queried by
        other agents in the OEF.

        :param service_description: description of the services to add
        :return: ``None``
        """

    @abstractmethod
    def send_message(self, dialogue_id: int, destination: str, msg: bytes) -> None:
        """
        Send a simple message.

        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param destination: the agent identifier to whom the message is sent.
        :param msg: the message (in bytes).
        :return: ``None``
        """

    @abstractmethod
    def send_cfp(self, dialogue_id: int, destination: str, query: CFP_TYPES, msg_id: Optional[int] = 1,
                 target: Optional[int] = 0) -> None:
        """
        Send a Call-For-Proposals.

        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param destination: the agent identifier to whom the message is sent.
        :param query: the query associated with the Call For Proposals.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def send_propose(self, dialogue_id: int, destination: str, proposals: PROPOSE_TYPES, msg_id: int,
                     target: Optional[int] = None) -> None:
        """
        Send a Propose.

        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param destination: the agent identifier to whom the message is sent.
        :param proposals: either a list of :class:`~oef.schema.Description` or ``bytes``.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def send_accept(self, dialogue_id: int, destination: str, msg_id: int,
                    target: Optional[int] = None) -> None:
        """
        Send an Accept.

        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param destination: the agent identifier to whom the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def send_decline(self, dialogue_id: int, destination: str, msg_id: int,
                     target: Optional[int] = None) -> None:
        """
        Send a Decline.

        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param destination: the agent identifier to whom the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def stop(self):
        """Stop the proxy."""

class DialogueInterface(ABC):
    """
    The methods of this interface are the callbacks that are called from the OEFProxy
    when a certain message has to be delivered to an agent.
    The names of the method match the pattern 'on' followed by the name of the message.
    """

    @abstractmethod
    def on_message(self, origin: str,
                   dialogue_id: int,
                   content: bytes) -> None:
        """
        Handler for simple messages.

        :param origin: the identifier of the agent who sent the message.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param content: the content of the message (in bytes).
        :return: ``None``
        """

    @abstractmethod
    def on_cfp(self, origin: str,
               dialogue_id: int,
               msg_id: int,
               target: int,
               query: CFP_TYPES) -> None:
        """
        Handler for CFP messages.

        :param origin: the identifier of the agent who sent the message.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param query: the query associated with the Call For Proposals.
        :return: ``None``
        """

    @abstractmethod
    def on_propose(self, origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int,
                   proposal: PROPOSE_TYPES) -> None:
        """
        Handler for Propose messages.

        :param origin: the identifier of the agent who sent the message.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param proposal: the proposal associated with the message.
        :return: ``None``
        """

    @abstractmethod
    def on_accept(self, origin: str,
                  dialogue_id: int,
                  msg_id: int,
                  target: int) -> None:
        """
        Handler for Accept messages.

        :param origin: the identifier of the agent who sent the message.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def on_decline(self, origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int) -> None:
        """
        Handler for Decline messages.

        :param origin: the identifier of the agent who sent the message.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """


class ConnectionInterface(ABC):
    """Methods to handle error and search result messages from the OEF Node."""

    @abstractmethod
    def on_error(self, operation: agent_pb2.Server.AgentMessage.Error.Operation,
                 dialogue_id: int,
                 message_id: int) -> None:
        """
        Handler for Error messages.

        :param operation: the operation
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param message_id: the message identifier for the dialogue.
        :return: ``None``
        """

    @abstractmethod
    def on_search_result(self, search_id: int, agents: List[str]) -> None:
        """
        Handler for Search Result messages.

        :param search_id: the identifier of the search to whom the result is answering.
        :param agents: the list of identifiers of the agents compliant with the search constraints.
        :return: ``None``
        """


class AgentInterface(DialogueInterface, ConnectionInterface, OEFCoreInterface, ABC):
    """
    Interface to be implemented by agents.
    It contains methods from:

    * DialogueInterface, that contains handlers for the incoming messages from other agents
    * ConnectionInterface, that contains handlers for error and search result messages from the OEF.
    * OEFCoreInterface, that contains methods for interact with the OEF and other agents.
    """
    pass


class OEFProxy(OEFCoreInterface, ABC):
    """Abstract definition of an OEF Proxy."""

    def __init__(self, public_key):
        self._public_key = public_key

    @property
    def public_key(self) -> str:
        """The public key used by the proxy to communicate with the OEF Node."""
        return self._public_key

    @abstractmethod
    async def _receive(self) -> bytes:
        """
        Receive a message from the OEF Node

        :return: the bytes received from the communication channel.
        """

    async def loop(self, agent: AgentInterface) -> None:  # noqa: C901
        """
        Event loop to wait for messages and to dispatch the arrived messages to the proper handler.

        :param agent: the implementation of the message handlers specified in AgentInterface.
        :return: ``None``
        """
        while True:
            try:
                data = await self._receive()
            except asyncio.CancelledError:
                logger.debug("Proxy {}: loop cancelled".format(self.public_key))
                break
            msg = agent_pb2.Server.AgentMessage()
            msg.ParseFromString(data)
            case = msg.WhichOneof("payload")
            logger.debug("loop {0}".format(case))
            if case == "agents":
                agent.on_search_result(msg.agents.search_id, msg.agents.agents)
            elif case == "error":
                agent.on_error(msg.error.operation, msg.error.dialogue_id, msg.error.msg_id)
            elif case == "content":
                content_case = msg.content.WhichOneof("payload")
                logger.debug("msg content {0}".format(content_case))
                if content_case == "content":
                    agent.on_message(msg.content.origin, msg.content.dialogue_id, msg.content.content)
                elif content_case == "fipa":
                    fipa = msg.content.fipa
                    fipa_case = fipa.WhichOneof("msg")
                    if fipa_case == "cfp":
                        cfp_case = fipa.cfp.WhichOneof("payload")
                        if cfp_case == "nothing":
                            query = None
                        elif cfp_case == "content":
                            query = fipa.cfp.content
                        elif cfp_case == "query":
                            query = Query.from_pb(fipa.cfp.query)
                        else:
                            raise Exception("Query type not valid.")
                        agent.on_cfp(msg.content.origin, msg.content.dialogue_id, fipa.msg_id, fipa.target, query)
                    elif fipa_case == "propose":
                        propose_case = fipa.propose.WhichOneof("payload")
                        if propose_case == "content":
                            proposals = fipa.propose.content
                        else:
                            proposals = [Description.from_pb(propose) for propose in fipa.propose.proposals.objects]
                        agent.on_propose(msg.content.origin, msg.content.dialogue_id, fipa.msg_id, fipa.target,
                                         proposals)
                    elif fipa_case == "accept":
                        agent.on_accept(msg.content.origin, msg.content.dialogue_id, fipa.msg_id, fipa.target)
                    elif fipa_case == "decline":
                        agent.on_decline(msg.content.origin, msg.content.dialogue_id, fipa.msg_id, fipa.target)
                    else:
                        logger.warning("Not implemented yet: fipa {0}".format(fipa_case))
