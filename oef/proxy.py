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
from typing import Optional, Awaitable, Tuple, List, Dict

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
    """
    This exception is used whenever an error occurs during the connection to the OEF Node.
    """


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

    def is_connected(self) -> bool:
        """
        Check if the proxy is currently connected to the OEF Node.

        :return: ``True`` if the proxy is connected, ``False`` otherwise.
        """
        return self._connection is not None

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
        if self._server_writer is None:
            raise OEFConnectionError("Connection not established yet. Please use 'connect()'.")
        serialized_msg = protobuf_msg.SerializeToString()
        nbytes = struct.pack("I", len(serialized_msg))
        self._server_writer.write(nbytes)
        self._server_writer.write(serialized_msg)

    async def _receive(self):
        """
        Receive a Protobuf message.

        :return: ``None``
        :raises OEFConnectionError: if the connection has not been established yet.
        """
        if self._server_reader is None:
            raise OEFConnectionError("Connection not established yet. Please use 'connect()'.")
        nbytes_packed = await self._server_reader.read(len(struct.pack("I", 0)))
        logger.debug("received ${0}".format(nbytes_packed))
        nbytes = struct.unpack("I", nbytes_packed)[0]
        logger.debug("received unpacked ${0}".format(nbytes))
        logger.debug("Preparing to receive ${0} bytes ...".format(nbytes))
        data = b""
        while len(data) < nbytes:
            data += await self._server_reader.read(nbytes - len(data))
            logger.debug("Read bytes: {}".format(len(data)))
        return data

    async def connect(self) -> bool:
        if self.is_connected() and not self._server_writer.transport.is_closing():
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

    def register_agent(self, msg_id: int, agent_description: Description):
        msg = RegisterDescription(msg_id, agent_description)
        self._send(msg.to_envelope())

    def register_service(self, msg_id: int, service_description: Description):
        msg = RegisterService(msg_id, service_description)
        self._send(msg.to_envelope())

    def unregister_agent(self, msg_id: int):
        msg = UnregisterDescription(msg_id)
        self._send(msg.to_envelope())

    def unregister_service(self, msg_id: int, service_description: Description):
        msg = UnregisterService(msg_id, service_description)
        self._send(msg.to_envelope())

    def search_agents(self, search_id: int, query: Query) -> None:
        msg = SearchAgents(search_id, query)
        self._send(msg.to_envelope())

    def search_services(self, search_id: int, query: Query) -> None:
        msg = SearchServices(search_id, query)
        self._send(msg.to_envelope())

    def send_message(self, msg_id: int, dialogue_id: int, destination: str, msg: bytes) -> None:
        msg = Message(msg_id, dialogue_id, destination, msg)
        self._send(msg.to_envelope())

    def send_cfp(self, msg_id: int, dialogue_id: int, destination: str, target: int, query: CFP_TYPES):
        msg = CFP(msg_id, dialogue_id, destination, target, query)
        self._send(msg.to_envelope())

    def send_propose(self, msg_id: int, dialogue_id: int, destination: str, target: int, proposals: PROPOSE_TYPES):
        msg = Propose(msg_id, dialogue_id, destination, target, proposals)
        self._send(msg.to_envelope())

    def send_accept(self, msg_id: int, dialogue_id: int, destination: str, target: int):
        msg = Accept(msg_id, dialogue_id, destination, target)
        self._send(msg.to_envelope())

    def send_decline(self, msg_id: int, dialogue_id: int, destination: str, target: int):
        msg = Decline(msg_id, dialogue_id, destination, target)
        self._send(msg.to_envelope())

    async def stop(self) -> None:
        """
        Tear down resources associated with this Proxy, i.e. the writing connection with the server.
        """
        await self._server_writer.drain()
        self._server_writer.close()
        self._server_writer = None
        self._server_reader = None
        self._connection = None


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

            self._read_queue = asyncio.Queue()  # type: asyncio.Queue
            self._queues = {}  # type: Dict[str, asyncio.Queue]
            self.loop = asyncio.get_event_loop()

        def __enter__(self):
            self._task = asyncio.ensure_future(self.run())
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()

        def connect(self, public_key: str) -> Optional[Tuple[asyncio.Queue, asyncio.Queue]]:
            """
            Connect a public key to the node.

            :param public_key: the public key of the agent.
            :return: an asynchronous queue, that constitutes the communication channel.
            """
            if public_key in self._queues:
                return None

            queue = asyncio.Queue()
            self._queues[public_key] = queue
            return self._read_queue, queue

        async def _process_messages(self) -> None:
            """
            Main event loop to process the incoming messages.

            :return: ``None``
            """
            while True:
                try:
                    data = await self._read_queue.get()  # type: Tuple[str, BaseMessage]
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
                asyncio.get_event_loop().run_until_complete(self._task)

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
            :param service_description: the description of the service agent to be unregistered.
            :return: ``None``
            """
            self.loop.run_until_complete(self._lock.acquire())
            self.services[public_key].remove(service_description)
            if len(self.services[public_key]) == 0:
                self.services.pop(public_key)
            self._lock.release()

        def search_agents(self, public_key: str, search_id: int, query: Query) -> None:
            """
            Search the agents in the local Agent Directory, and send back the result.
            The provided query will be checked with every instance of the Agent Directory.

            :param public_key: the source of the search request.
            :param search_id: the search identifier associated with the search request.
            :param query: the query that constitutes the search.
            :return: ``None``
            """

            result = []
            for agent_public_key, description in self.agents.items():
                if query.check(description):
                    result.append(agent_public_key)

            self._send_search_result(public_key, search_id, sorted(set(result)))

        def search_services(self, public_key: str, search_id: int, query: Query) -> None:
            """
            Search the agents in the local Service Directory, and send back the result.
            The provided query will be checked with every instance of the Agent Directory.

            :param public_key: the source of the search request.
            :param search_id: the search identifier associated with the search request.
            :param query: the query that constitutes the search.
            :return: ``None``
            """

            result = []
            for agent_public_key, descriptions in self.services.items():
                for description in descriptions:
                    if query.check(description):
                        result.append(agent_public_key)

            self._send_search_result(public_key, search_id, sorted(set(result)))

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
            new_msg.answer_id = msg.msg_id
            new_msg.content.origin = origin
            new_msg.content.dialogue_id = e.send_message.dialogue_id

            payload = e.send_message.WhichOneof("payload")
            if payload == "content":
                new_msg.content.content = e.send_message.content
            elif payload == "fipa":
                new_msg.content.fipa.CopyFrom(e.send_message.fipa)

            self._queues[destination].put_nowait(new_msg.SerializeToString())

        def _send_search_result(self, public_key: str, search_id: int, agents: List[str]) -> None:
            """
            Send a search result.

            :param public_key: the public key of the agent to whom to send the search result.
            :param search_id: the id of the search request.
            :param agents: the list of public key of the agents/services to be returned.
            :return: ``None``
            """
            msg = agent_pb2.Server.AgentMessage()
            msg.answer_id = search_id
            msg.agents.agents.extend(agents)
            self._queues[public_key].put_nowait(msg.SerializeToString())

    def __init__(self, public_key: str, local_node: LocalNode):
        """
        Initialize a OEF proxy for a local OEF Node (that is, :class:`~oef.proxy.OEFLocalProxy.LocalNode`

        :param public_key: the public key used in the protocols.
        :param local_node: the Local OEF Node object. This reference must be the same across the agents of interest.
        """

        super().__init__(public_key)
        self.local_node = local_node
        self._connection = None
        self._read_queue = None
        self._write_queue = None

    def register_agent(self, msg_id: int, agent_description: Description) -> None:
        self.local_node.register_agent(self.public_key, agent_description)

    def register_service(self, msg_id: int, service_description: Description) -> None:
        self.local_node.register_service(self.public_key, service_description)

    def search_agents(self, search_id: int, query: Query) -> None:
        self.local_node.search_agents(self.public_key, search_id, query)

    def search_services(self, search_id: int, query: Query) -> None:
        self.local_node.search_services(self.public_key, search_id, query)

    def unregister_agent(self, msg_id: int) -> None:
        self.local_node.unregister_agent(self.public_key)

    def unregister_service(self, msg_id: int, service_description: Description) -> None:
        self.local_node.unregister_service(self.public_key, service_description)

    def send_message(self, msg_id: int, dialogue_id: int, destination: str, msg: bytes):
        msg = Message(msg_id, dialogue_id, destination, msg)
        self._send(msg)

    def send_cfp(self, msg_id: int, dialogue_id: int, destination: str, target: int, query: CFP_TYPES) -> None:
        msg = CFP(msg_id, dialogue_id, destination, target, query)
        self._send(msg)

    def send_propose(self, msg_id: int, dialogue_id: int, destination: str, target: int,
                     proposals: PROPOSE_TYPES) -> None:
        msg = Propose(msg_id, dialogue_id, destination, target, proposals)
        self._send(msg)

    def send_accept(self, msg_id: int, dialogue_id: int, destination: str, target: int) -> None:
        msg = Accept(msg_id, dialogue_id, destination, target)
        self._send(msg)

    def send_decline(self, msg_id: int, dialogue_id: int, destination: str, target: int) -> None:
        msg = Decline(msg_id, dialogue_id, destination, target)
        self._send(msg)

    async def connect(self) -> bool:
        if self._connection is not None:
            return True

        self._connection = self.local_node.connect(self.public_key)
        if self._connection is None:
            return False
        self._write_queue, self._read_queue = self._connection
        return True

    async def _receive(self) -> bytes:
        data = await self._read_queue.get()
        return data

    def _send(self, msg: BaseMessage) -> None:
        self._write_queue.put_nowait((self.public_key, msg))

    async def stop(self):
        self._connection = None
        self._read_queue = None
        self._write_queue = None

    def is_connected(self) -> bool:
        return self._connection is not None
