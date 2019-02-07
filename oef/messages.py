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
oef.messages
~~~~~~~~~~~~

This module contains classes to manage serialization of data in Protobuf messages.

"""

from abc import ABC, abstractmethod
from typing import Optional, Union, List

from enum import Enum

from oef.schema import Description

from oef import agent_pb2, fipa_pb2
from oef.query import Query

NoneType = type(None)
CFP_TYPES = Union[Query, bytes, NoneType]
PROPOSE_TYPES = Union[bytes, List[Description]]


class OEFErrorOperation(Enum):
    """Operation code for the OEF. It is returned in the OEF Error messages."""
    REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    REGISTER_DESCRIPTION = 2
    UNREGISTER_DESCRIPTION = 3


class BaseMessage(ABC):
    """
    An abstract class to represent the messages exchanged with the OEF.
    Every subclass must implement the :func:`~oef.messages.to_envelope` method
    that serialize the data into a protobuf message.
    """

    def __init__(self, msg_id):
        """
        Initialize a message.

        :param msg_id: the identifier of the message.
        """
        self.msg_id = msg_id

    @abstractmethod
    def to_envelope(self) -> agent_pb2.Envelope:
        """
        Pack the message into a protobuf message.

        :return: the envelope.
        """


class RegisterDescription(BaseMessage):
    """
    This message is used for registering a new agent  in the Agent Directory of an OEF Node.
    The agent is described by a :class:`~oef.schema.Description` object.

    It is used in the method :func:`~oef.core.OEFCoreInterface.register_agent`.
    """

    def __init__(self, msg_id: int, agent_description: Description):
        """
        Initialize a RegisterDescription message.

        :param msg_id: the identifier of the message.
        :param agent_description: the agent's description.
        """
        super().__init__(msg_id)
        self.agent_description = agent_description

    def to_envelope(self) -> agent_pb2.Envelope:
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.register_description.CopyFrom(self.agent_description.to_agent_description_pb())
        return envelope


class RegisterService(BaseMessage):
    """
    This message is used for registering a new agent in the Service Directory of an OEF Node.
    The service agent is described by a :class:`~oef.schema.Description` object.

    It is used in the method :func:`~oef.core.OEFCoreInterface.register_service`.
    """

    def __init__(self, msg_id: int, service_description: Description):
        """
        Initialize a RegisterService message.

        :param msg_id: the identifier of the message.
        :param service_description: the service agent's description.
        """
        super().__init__(msg_id)
        self.service_description = service_description

    def to_envelope(self) -> agent_pb2.Envelope:
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.register_service.CopyFrom(self.service_description.to_agent_description_pb())
        return envelope


class UnregisterDescription(BaseMessage):
    """
    This message is used for unregistering an agent in the Agent Directory of an OEF Node.

    It is used in the method :func:`~oef.core.OEFCoreInterface.unregister_agent`.
    """

    def __init__(self, msg_id: int):
        """Initialize a UnregisterDescription message.

        :param msg_id: the identifier of the message.
        """
        super().__init__(msg_id)

    def to_envelope(self) -> agent_pb2.Envelope:
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.unregister_description.CopyFrom(agent_pb2.Envelope.Nothing())
        return envelope


class UnregisterService(BaseMessage):
    """
    This message is used for unregistering a `(service agent, description)` in the Service Directory of an OEF Node.
    The service agent is described by a :class:`~oef.schema.Description` object.

    It is used in the method :func:`~oef.core.OEFCoreInterface.unregister_service`.
    """

    def __init__(self, msg_id: int, service_description):
        """
        Initialize a UnregisterService message.

        :param msg_id: the identifier of the message.
        :param service_description: the service agent's description.
        """
        super().__init__(msg_id)
        self.service_description = service_description

    def to_envelope(self) -> agent_pb2.Envelope:
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.unregister_service.CopyFrom(self.service_description.to_agent_description_pb())
        return envelope


class SearchAgents(BaseMessage):
    """
    This message is used for searching agents in the Agent Directory of an OEF Node.
    It contains:

    * a search id, that identifies the search query. This id will be used
      by the sender in order to distinguish different incoming search results.
    * a query, i.e. a list of constraints defined over a data model.

    If everything works correctly, eventually, the sender of the message will receive a
    search result message and the agent's :func:`~oef.core.OEFCoreInterface.on_search_result` will be executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.search_agents`.
    """

    def __init__(self, msg_id: int, query: Query):
        """
        Initialize a SearchAgents message.

        :param msg_id: the identifier of the message.
        :param query: the query that describe the agent we are looking for.
        """
        super().__init__(msg_id)
        self.query = query

    def to_envelope(self):
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.search_agents.query.CopyFrom(self.query.to_pb())
        return envelope


class SearchServices(BaseMessage):
    """
    This message is used for searching services in the Service Directory of an OEF Node.
    It contains:

    * a search id, that identifies the search query. This id will be used
      by the sender in order to distinguish different incoming search results.
    * a query, i.e. a list of constraints defined over a data model.

    If everything works correctly, eventually, the sender of the message will receive a
    search result message and the agent's :func:`~oef.core.OEFCoreInterface.on_search_result` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.search_services`.
    """

    def __init__(self, msg_id: int, query: Query):
        """
        Initialize a SearchServices message.

        :param msg_id: the identifier of the message.
        :param query: the query that describe the agent we are looking for.
        """
        super().__init__(msg_id)
        self.query = query

    def to_envelope(self) -> agent_pb2.Envelope:
        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.search_services.query.CopyFrom(self.query.to_pb())
        return envelope


class AgentMessage(BaseMessage, ABC):
    """
    This type of message is used for interacting with other agents, via an OEF Node.
    There are five different type of agent messages:

    1. :class:`.Message`, to convey a generic message (that is, a sequence of bytes).
    2. :class:`.CFP`, to make a `Call For Proposals` for some resources.
    3. :class:`.Propose`, to make a `Proposal` about a specific resource.
    4. :class:`.Accept`, to accept a previous `Proposal`.
    5. :class:`.Decline`, to decline the negotiation.

    Using message 1 is the most generic way to interact with other OEF agent. It is flexible, but requires
    extra development efforts to come up with a working protocol.

    Messages 2-5 are used in the negotiation protocol, where some agents are buyers and other are sellers.
    The protocol is compliant with FIPA specifications.
    """


class Message(AgentMessage):
    """
    This message is used to send a generic message to other agents.
    It contains:

    * a dialogue id, that identifies the dialogue in which the message is sent.
    * a destination, that is the public key of the recipient of the message.
    * a sequence of bytes, that is the content of the message.

    If everything works correctly, eventually, the recipient will receive the content of the message
     and the recipient's :func:`~oef.core.OEFCoreInterface.on_message` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.send_message`.
    """

    def __init__(self, msg_id: int,
                 dialogue_id: int,
                 destination: str,
                 msg: bytes):
        """
        Initialize a simple message.

        :param msg_id: the identifier of the message.
        :param dialogue_id: the identifier of the dialogue.
        :param destination: the public key of the recipient agent.
        :param msg: the content of the message.
        """
        super().__init__(msg_id)
        self.dialogue_id = dialogue_id
        self.destination = destination
        self.msg = msg

    def to_envelope(self) -> agent_pb2.Envelope:
        agent_msg = agent_pb2.Agent.Message()
        agent_msg.dialogue_id = self.dialogue_id
        agent_msg.destination = self.destination
        agent_msg.content = self.msg

        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.send_message.CopyFrom(agent_msg)
        return envelope


class CFP(AgentMessage):
    """
    This message is used to send a `Call For Proposals`.
    It contains:

    * a message id, that is an unique identifier for a message, given the dialogue.
    * a dialogue id, that identifies the dialogue in which the message is sent.
    * a destination, that is the public key of the recipient of the message.
    * a target id, that is, the identifier of the message to whom this message is targeting, in a given dialogue.
    * a query, that describes the resources the sender is interested in.

    If everything works correctly, eventually, the recipient will receive the content of the message
    and the recipient's :func:`~oef.core.OEFCoreInterface.on_cfp` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.send_cfp`.
    """

    def __init__(self, msg_id: int,
                 dialogue_id: int,
                 destination: str,
                 target: int,
                 query: CFP_TYPES):
        """
        Initialize a `Call For Proposal` message.

        :param msg_id: the unique identifier of the message in the dialogue denoted by ``dialogue_id``.
        :param dialogue_id: the identifier of the dialogue.
        :param destination: the public key of the recipient agent.
        :param target: the identifier of the message to whom this message is targeting.
        :param query: the query, an instance of `~oef.schema.Query`, ``bytes``, or ``None``.
        """
        super().__init__(msg_id)
        self.dialogue_id = dialogue_id
        self.destination = destination
        self.query = query
        self.target = target

    def to_envelope(self) -> agent_pb2.Agent.Message:
        fipa_msg = fipa_pb2.Fipa.Message()
        fipa_msg.target = self.target
        cfp = fipa_pb2.Fipa.Cfp()

        if self.query is None:
            cfp.nothing.CopyFrom(fipa_pb2.Fipa.Cfp.Nothing())
        elif isinstance(self.query, Query):
            cfp.query.CopyFrom(self.query.to_pb())
        elif isinstance(self.query, bytes):
            cfp.content = self.query
        fipa_msg.cfp.CopyFrom(cfp)
        agent_msg = agent_pb2.Agent.Message()
        agent_msg.dialogue_id = self.dialogue_id
        agent_msg.destination = self.destination
        agent_msg.fipa.CopyFrom(fipa_msg)

        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.send_message.CopyFrom(agent_msg)
        return envelope


class Propose(AgentMessage):
    """
    This message is used to send a `Propose`.
    It contains:

    * the message id, that is an unique identifier for a message, given dialogue.
    * a dialogue id, that identifies the dialogue in which the message is sent.
    * a destination, that is the public key of the recipient of the message.
    * target, that is, the identifier of the message to whom this message is targeting.
    * a list of proposals describing the resources that the seller proposes.

    If everything works correctly, eventually, the recipient will receive the content of the message
    and the recipient's :func:`~oef.core.OEFCoreInterface.on_propose` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.send_propose`.
    """

    def __init__(self, msg_id: int,
                 dialogue_id: int,
                 destination: str,
                 target: int,
                 proposals: PROPOSE_TYPES):
        """
        Initialize a `Propose` message.

        :param msg_id: the unique identifier of the message in the dialogue denoted by ``dialogue_id``.
        :param dialogue_id: the identifier of the dialogue.
        :param destination: the public key of the recipient agent.
        :param target: the identifier of the message to whom this message is targeting.
        :param proposals: a list of proposals. A proposal can be a `~oef.schema.Description` or ``bytes``.
        """

        super().__init__(msg_id)
        self.dialogue_id = dialogue_id
        self.destination = destination
        self.target = target
        self.proposals = proposals

    def to_envelope(self) -> agent_pb2.Agent.Message:
        fipa_msg = fipa_pb2.Fipa.Message()
        fipa_msg.target = self.target
        propose = fipa_pb2.Fipa.Propose()
        if isinstance(self.proposals, bytes):
            propose.content = self.proposals
        else:
            proposals_pb = fipa_pb2.Fipa.Propose.Proposals()
            proposals_pb.objects.extend([propose.to_pb() for propose in self.proposals])
            propose.proposals.CopyFrom(proposals_pb)
        fipa_msg.propose.CopyFrom(propose)
        agent_msg = agent_pb2.Agent.Message()
        agent_msg.dialogue_id = self.dialogue_id
        agent_msg.destination = self.destination
        agent_msg.fipa.CopyFrom(fipa_msg)

        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.send_message.CopyFrom(agent_msg)
        return envelope


class Accept(AgentMessage):
    """
    This message is used to send an `Accept`.
    It contains:

    * the message id, that is an unique identifier for a message, given dialogue.
    * a dialogue id, that identifies the dialogue in which the message is sent.
    * a destination, that is the public key of the recipient of the message.
    * target, that is, the identifier of the message to whom this message is targeting.

    If everything works correctly, eventually, the recipient will receive the content of the message
    and the recipient's :func:`~oef.core.OEFCoreInterface.on_accept` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.send_accept`.
    """

    def __init__(self, msg_id: int,
                 dialogue_id: int,
                 destination: str,
                 target: int):
        """
        Initialize an `Accept` message.

        :param dialogue_id: the identifier of the dialogue.
        :param destination: the public key of the recipient agent.
        :param msg_id: the unique identifier of the message in the dialogue denoted by ``dialogue_id``.
        :param target: the identifier of the message to whom this message is targeting.
        """
        super().__init__(msg_id)
        self.dialogue_id = dialogue_id
        self.destination = destination
        self.target = target

    def to_envelope(self) -> agent_pb2.Agent.Message:
        fipa_msg = fipa_pb2.Fipa.Message()
        fipa_msg.target = self.target
        accept = fipa_pb2.Fipa.Accept()
        fipa_msg.accept.CopyFrom(accept)
        agent_msg = agent_pb2.Agent.Message()
        agent_msg.dialogue_id = self.dialogue_id
        agent_msg.destination = self.destination
        agent_msg.fipa.CopyFrom(fipa_msg)

        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.send_message.CopyFrom(agent_msg)
        return envelope


class Decline(AgentMessage):
    """
    This message is used to send an `Decline`.
    It contains:

    * the message id, that is an unique identifier for a message, given dialogue.
    * a dialogue id, that identifies the dialogue in which the message is sent.
    * a destination, that is the public key of the recipient of the message.
    * target, that is, the identifier of the message to whom this message is targeting.

    If everything works correctly, eventually, the recipient will receive the content of the message
    and the recipient's :func:`~oef.core.OEFCoreInterface.on_decline` is executed.

    It is used in the method :func:`~oef.core.OEFCoreInterface.send_decline`.
    """

    def __init__(self, msg_id: int,
                 dialogue_id: int,
                 destination: str,
                 target: int):
        """
        Initialize a `Decline` message.

        :param dialogue_id: the identifier of the dialogue.
        :param destination: the public key of the recipient agent.
        :param msg_id: the unique identifier of the message in the dialogue denoted by ``dialogue_id``.
        :param target: the identifier of the message to whom this message is targeting.
        """

        super().__init__(msg_id)
        self.dialogue_id = dialogue_id
        self.destination = destination
        self.target = target

    def to_envelope(self):
        fipa_msg = fipa_pb2.Fipa.Message()
        fipa_msg.target = self.target
        decline = fipa_pb2.Fipa.Decline()
        fipa_msg.decline.CopyFrom(decline)
        agent_msg = agent_pb2.Agent.Message()
        agent_msg.dialogue_id = self.dialogue_id
        agent_msg.destination = self.destination
        agent_msg.fipa.CopyFrom(fipa_msg)

        envelope = agent_pb2.Envelope()
        envelope.msg_id = self.msg_id
        envelope.send_message.CopyFrom(agent_msg)
        return envelope
