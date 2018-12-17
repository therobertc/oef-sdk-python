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

oef.proxy
~~~~~~~~~

This module defines the proxies classes used by agents to interact with an OEF Node.

"""

import asyncio
import logging
import struct
from collections import defaultdict
from typing import Optional, Awaitable, Tuple, List

import oef.agent_pb2 as agent_pb2
from oef.core import OEFProxy
from oef.messages import Message, CFP_TYPES, PROPOSE_TYPES, CFP, Propose, Accept, Decline, BaseMessage, \
    AgentMessage, RegisterDescription, RegisterService, UnregisterDescription, \
    UnregisterService, SearchAgents, SearchServices
from oef.query import Query
from oef.schema import Description

logger = logging.getLogger(__name__)


DEFAULT_OEF_NODE_PORT = 3333


class OEFConnectionError(ConnectionError):
    pass


class OEFNetworkProxy(OEFProxy):
    """
    Proxy to the functionality of the OEF. Provides functionality for an agent to:

     * Register a description of itself
     * Register its services
     * Locate other agents
     * Locate other services
     * Establish a connection with another agent
    """

    def __init__(self, public_key: str, oef_addr: str, port: int = DEFAULT_OEF_NODE_PORT) -> None:
        """
        Initialize the proxy to the OEF Node.

        :param public_key: the public key used in the protocols.
        :param oef_addr: the IP address of the OEF node.
        :param port: port number for the connection.
        """
        super().__init__(public_key)

        self.oef_addr = oef_addr
        self.port = port

        # these are setup in _connect_to_server
        self._connection = None
        self._server_reader = None
        self._server_writer = None

    async def _connect_to_server(self, event_loop) -> Awaitable[Tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
        """
        Connect to the OEF Node.

        :param event_loop: the event loop to use for the connection.
        :return: A stream reader and a stream writer for the connection.
        """
        return await asyncio.open_connection(self.oef_addr, self.port, loop=event_loop)

    def _send(self, protobuf_msg) -> None:
        """
        Send a Protobuf message to a previously established connection.

        :param protobuf_msg: the message to be sent
        :return: ``None``
        :raises OEFConnectionError: if the connection has not been established yet.
        """
        try:
            assert self._server_writer is not None
        except AssertionError:
            raise OEFConnectionError("Connection not established yet. Please use 'connect()'.")
        serialized_msg = protobuf_msg.SerializeToString()
        nbytes = struct.pack("I", len(serialized_msg))
        self._server_writer.write(nbytes)
        self._server_writer.write(serialized_msg)

    async def _receive(self):
        """
        Send a Protobuf message.

        :param protobuf_msg: the message to be sent
        :return: ``None``
        :raises OEFConnectionError: if the connection has not been established yet.
        """
        try:
            assert self._server_reader is not None
        except AssertionError:
            raise OEFConnectionError("Connection not established yet. Please use 'connect()'.")
        nbytes_packed = await self._server_reader.read(len(struct.pack("I", 0)))
        logger.debug("received ${0}".format(nbytes_packed))
        nbytes = struct.unpack("I", nbytes_packed)
        logger.debug("received unpacked ${0}".format(nbytes[0]))
        logger.debug("Preparing to receive ${0} bytes ...".format(nbytes[0]))
        return await self._server_reader.read(nbytes[0])

    async def connect(self) -> bool:
        if self._connection is not None:
            return True

        event_loop = asyncio.get_event_loop()
        self._connection = await self._connect_to_server(event_loop)
        self._server_reader, self._server_writer = self._connection
        # Step 1: Agent --(ID)--> OEFCore
        pb_public_key = agent_pb2.Agent.Server.ID()
        pb_public_key.public_key = self.public_key
        self._send(pb_public_key)
        # Step 2: OEFCore --(Phrase)--> Agent
        data = await self._receive()
        pb_phrase = agent_pb2.Server.Phrase()
        pb_phrase.ParseFromString(data)
        case = pb_phrase.WhichOneof("payload")
        if case == "failure":
            return False
        # Step 3: Agent --(Answer)--> OEFCore
        pb_answer = agent_pb2.Agent.Server.Answer()
        pb_answer.answer = pb_phrase.phrase[::-1]
        self._send(pb_answer)
        # Step 4: OEFCore --(Connected)--> Agent
        data = await self._receive()
        pb_status = agent_pb2.Server.Connected()
        pb_status.ParseFromString(data)
        return pb_status.status

    def register_agent(self, agent_description: Description) -> None:
        msg = RegisterDescription(agent_description)
        self._send(msg.to_envelope())

    def register_service(self, service_description: Description) -> None:
        msg = RegisterService(service_description)
        self._send(msg.to_envelope())

    def unregister_agent(self) -> None:
        msg = UnregisterDescription()
        self._send(msg.to_envelope())

    def unregister_service(self, service_description: Description) -> None:
        msg = UnregisterService(service_description)
        self._send(msg.to_envelope())

    def search_agents(self, search_id: int, query: Query) -> None:
        msg = SearchAgents(search_id, query)
        self._send(msg.to_envelope())

    def search_services(self, search_id: int, query: Query) -> None:
        msg = SearchServices(search_id, query)
        self._send(msg.to_envelope())

    def send_message(self, dialogue_id: int, destination: str, msg: bytes) -> None:
        msg = Message(dialogue_id, destination, msg)
        self._send(msg.to_envelope())

    def send_cfp(self, dialogue_id: int,
                 destination: str,
                 query: CFP_TYPES,
                 msg_id: Optional[int] = 1,
                 target: Optional[int] = 0) -> None:
        msg = CFP(dialogue_id, destination, query, msg_id, target)
        self._send(msg.to_envelope())

    def send_propose(self, dialogue_id: int,
                     destination: str,
                     proposals: PROPOSE_TYPES,
                     msg_id: int,
                     target: Optional[int] = None) -> None:
        msg = Propose(dialogue_id, destination, proposals, msg_id, target)
        self._send(msg.to_envelope())

    def send_accept(self, dialogue_id: int, destination: str, msg_id: int,
                    target: Optional[int] = None) -> None:
        msg = Accept(dialogue_id, destination, msg_id, target)
        self._send(msg.to_envelope())

    def send_decline(self, dialogue_id: int,
                     destination: str,
                     msg_id: int,
                     target: Optional[int] = None) -> None:
        msg = Decline(dialogue_id, destination, msg_id, target)
        self._send(msg.to_envelope())

    def stop(self) -> None:
        """
        Tear down resources associated with this Proxy, i.e. the writing connection with the server.
        """
        self._server_writer.close()


class OEFLocalProxy(OEFProxy):
    """
    Proxy to the functionality of the OEF.
    It allows the interaction between agents, but not the search functionality.
    It is useful for local testing.
    """

    class LocalNode:
        """A light-weight local implementation of a OEF Node."""

        def __init__(self):
            """
            Initialize a local (i.e. non-networked) implementation of an OEF Node
            """
            self.agents = dict()                     # type: Dict[str, Description]
            self.services = defaultdict(lambda: [])  # type: Dict[str, List[Description]]
            self._lock = asyncio.Lock()
            self._task = None

            self.read_queue = asyncio.Queue()  # type: asyncio.Queue
            self.queues = {}  # type: Dict[str, asyncio.Queue]
            self.loop = asyncio.get_event_loop()

        def connect(self, public_key: str) -> Optional[asyncio.Queue]:
            """
            Connect a public key to the node.

            :param public_key: the public key of the agent.
            :return: an asynchronous queue, that constitutes the communication channel.
            """
            if public_key in self.queues:
                return None
            queue = asyncio.Queue()
            self.queues[public_key] = queue
            return queue

        async def _process_messages(self) -> None:
            """
            Main event loop to process the incoming messages.

            :return: ``None``
            """
            while True:
                try:
                    data = await self.read_queue.get()  # type: Tuple[str, BaseMessage]
                except asyncio.CancelledError:
                    logger.debug("Local Node: loop cancelled.")
                    break

                public_key, msg = data
                assert isinstance(msg, AgentMessage)
                self._send_agent_message(public_key, msg)

        async def run(self) -> None:
            """
            Run the node, i.e. start processing the messages.

            :return: ``None``
            """
            self._task = asyncio.ensure_future(self._process_messages())
            await self._task

        def stop(self) -> None:
            """
            Stop the execution of the node.

            :return: ``None``
            """
            if self._task:
                self._task.cancel()

        def register_agent(self, public_key: str, agent_description: Description) -> None:
            """
            Register an agent in the agent directory of the node.

            :param public_key: the public key of the agent to be registered.
            :param agent_description: the description of the agent to be registered.
            :return: ``None``
            """
            self.loop.run_until_complete(self._lock.acquire())
            self.agents[public_key] = agent_description
            self._lock.release()

        def register_service(self, public_key: str, service_description: Description):
            """
            Register a service agent in the service directory of the node.

            :param public_key: the public key of the service agent to be registered.
            :param service_description: the description of the service agent to be registered.
            :return: ``None``
            """
            self.loop.run_until_complete(self._lock.acquire())
            self.services[public_key].append(service_description)
            self._lock.release()

        def unregister_agent(self, public_key: str) -> None:
            """
            Unregister an agent.

            :param public_key: the public key of the agent to be unregistered.
            :return: ``None``
            """
            self.loop.run_until_complete(self._lock.acquire())
            self.agents.pop(public_key)
            self._lock.release()

        def unregister_service(self, public_key: str, service_description: Description) -> None:
            """
            Unregister a service agent.

            :param public_key: the public key of the service agent to be unregistered.
            :return: ``None``
            """
            self.loop.run_until_complete(self._lock.acquire())
            self.services[public_key].remove(service_description)
            if len(self.services[public_key]) == 0:
                self.services.pop(public_key)
            self._lock.release()

        def search_agents(self, public_key: str, search_id: int, query: Query) -> None:
            """Since the agent directory and the instance checking are not implemented,
            just send a dummy search result message, returning all the connected agents."""
            self._send_search_result(public_key, search_id, sorted(self.agents.keys()))

        def search_services(self, public_key: str, search_id: int, query: Query) -> None:
            """Since the service directory and the instance checking are not implemented,
            just send a dummy search result message, returning all the connected agents."""
            self._send_search_result(public_key, search_id, sorted(self.services.keys()))

        def _send_agent_message(self, origin: str, msg: AgentMessage) -> None:
            """
            Send an :class:`~oef.messages.AgentMessage`.

            :param origin: the public key of the sender agent.
            :param msg: the message.
            :return: ``None``
            """
            e = msg.to_envelope()
            destination = e.send_message.destination

            new_msg = agent_pb2.Server.AgentMessage()
            new_msg.content.origin = origin
            new_msg.content.dialogue_id = e.send_message.dialogue_id

            payload = e.send_message.WhichOneof("payload")
            if payload == "content":
                new_msg.content.content = e.send_message.content
            elif payload == "fipa":
                new_msg.content.fipa.CopyFrom(e.send_message.fipa)

            self.queues[destination].put_nowait(new_msg.SerializeToString())

        def _send_search_result(self, public_key: str, search_id: int, agents: List[str]) -> None:
            """
            Send a search result.

            :param public_key: the public key of the agent to whom to send the search result.
            :param search_id: the id of the search request.
            :param agents: the list of public key of the agents/services to be returned.
            :return:
            """
            msg = agent_pb2.Server.AgentMessage()
            msg.agents.search_id = search_id
            msg.agents.agents.extend(agents)
            self.queues[public_key].put_nowait(msg.SerializeToString())

    def __init__(self, public_key: str, local_node: LocalNode):
        super().__init__(public_key)
        self.local_node = local_node
        self.read_queue = asyncio.Queue()
        self.write_queue = self.local_node.read_queue

    def register_agent(self, agent_description: Description) -> None:
        self.local_node.register_agent(self.public_key, agent_description)

    def register_service(self, service_description: Description) -> None:
        self.local_node.register_service(self.public_key, service_description)

    def search_agents(self, search_id: int, query: Query) -> None:
        self.local_node.search_agents(self.public_key, search_id, query)

    def search_services(self, search_id: int, query: Query) -> None:
        self.local_node.search_services(self.public_key, search_id, query)

    def unregister_agent(self) -> None:
        self.local_node.unregister_agent(self.public_key)

    def unregister_service(self, service_description: Description) -> None:
        self.local_node.unregister_service(self.public_key, service_description)

    def send_message(self, dialogue_id: int, destination: str, msg: bytes) -> None:
        msg = Message(dialogue_id, destination, msg)
        self._send(msg)

    def send_cfp(self, dialogue_id: int, destination: str, query: CFP_TYPES, msg_id: Optional[int] = 1,
                 target: Optional[int] = 0) -> None:
        msg = CFP(dialogue_id, destination, query, msg_id, target)
        self._send(msg)

    def send_propose(self, dialogue_id: int, destination: str, proposals: PROPOSE_TYPES, msg_id: int,
                     target: Optional[int] = None) -> None:
        msg = Propose(dialogue_id, destination, proposals, msg_id, target)
        self._send(msg)

    def send_accept(self, dialogue_id: int, destination: str, msg_id: int, target: Optional[int] = None) -> None:
        msg = Accept(dialogue_id, destination, msg_id, target)
        self._send(msg)

    def send_decline(self, dialogue_id: int, destination: str, msg_id: int, target: Optional[int] = None) -> None:
        msg = Decline(dialogue_id, destination, msg_id, target)
        self._send(msg)

    async def connect(self) -> bool:
        queue = self.local_node.connect(self.public_key)
        if not queue:
            return False
        self.read_queue = queue
        return True

    async def _receive(self) -> bytes:
        data = await self.read_queue.get()
        return data

    def _send(self, msg: BaseMessage) -> None:
        self.write_queue.put_nowait((self.public_key, msg))

    def stop(self):
        pass
