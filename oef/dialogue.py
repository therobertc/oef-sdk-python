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

oef.dialogue
~~~~~~~~~~~~

This module contains classes to implement more complex dialogues.


"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional

from oef.messages import CFP_TYPES, PROPOSE_TYPES, OEFErrorOperation

from oef.agents import Agent
from oef.core import DialogueInterface, OEFProxy

import uuid

DialogueKey = Tuple[str, int]
DialogueAgent = None


class SingleDialogue(ABC):
    """
    This class is used to hold information about a dialogue with another agent.

    It implements the :class:`~oef.core.DialogueInterface`, so it is needed to implement all the message handlers
    (i.e. :func:`~oef.core.DialogueInerface.on_message`, :func:`~oef.core.DialogueInerface.on_cfp`...)
    """

    def __init__(self, agent: DialogueAgent,
                 destination: str,
                 id_: Optional[int] = None):
        """
        Initialize a single dialogue.

        :param agent: the agent who holds the dialogue.
        :param destination: the identifier of the agent participating in the dialogue
        :param id_: the identifier of this dialogue.
        """
        self.agent = agent
        self.destination = destination
        self.id = id_
        if id_ is not None:
            self.is_buyer = False
        else:
            self.id = uuid.uuid4().time_mid
            self.is_buyer = True

    @property
    def key(self) -> DialogueKey:
        """The identifier for this dialogue."""
        return self.destination, self.id

    @abstractmethod
    def on_message(self, msg_id: int, content: bytes) -> None:
        """
        Handler for simple messages. Analogous to the :func:`~oef.core.DialogueInterface.on_message` method.

        :param msg_id: the message identifier for the dialogue.
        :param content: the content of the message (in bytes).
        :return: ``None``
        """

    @abstractmethod
    def on_cfp(self, msg_id: int, target: int, query: CFP_TYPES) -> None:
        """
        Handler for CFP messages. Analogous to the:func:`~oef.core.DialogueInterface.on_cfp` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param query: the query associated with the Call For Proposals.
        """

    @abstractmethod
    def on_propose(self, msg_id: int, target: int, proposal: PROPOSE_TYPES) -> None:
        """
        Handler for Propose messages. Analogous to the:func:`~oef.core.DialogueInterface.on_propose` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param proposal: the proposal associated with the message.
        :return: ``None``
        """

    @abstractmethod
    def on_accept(self, msg_id: int, target: int) -> None:
        """
        Handler for Accept messages. Analogous to the:func:`~oef.core.DialogueInterface.on_accept` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def on_decline(self, msg_id: int, target: int) -> None:
        """
        Handler for Decline messages. Analogous to the:func:`~oef.core.DialogueInterface.on_decline` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """

    @abstractmethod
    def on_dialogue_error(self, answer_id: int, dialogue_id: int, origin: str) -> None:
        """
        Handler for error messages concerning dialogues between agents.
        Analogous to the:func:`~oef.core.ConnectionInterface.on_dialogue_error` method.

        :param answer_id: the id of the message that generated the error.
        :param dialogue_id: the identifier of the dialogue in which the message is sent.
        :param origin: the identifier of the agent that generated the error.
        :return: ``None``
        """

    def send_message(self, msg_id: int, msg: bytes) -> None:
        """
        Send a simple message. Analogous to the :func:`~oef.core.OEFCoreInterface.send_message` method.

        :param msg_id: the identifier of the message.
        :param msg: the message (in bytes).
        :return: ``None``
        """
        self.agent.send_message(msg_id, self.id, self.destination, msg)

    def send_cfp(self, msg_id: int, target: int, query: CFP_TYPES) -> None:
        """
        Send a Call-For-Proposals. Analogous to the :func:`~oef.core.OEFCoreInterface.send_cfp` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param query: the query associated with the Call For Proposals.
        :return: ``None``
        """
        self.agent.send_cfp(msg_id, self.id, self.destination, target, query)

    def send_propose(self, msg_id: int, target: int, proposals: PROPOSE_TYPES) -> None:
        """
        Send a Propose. Analogous to the :func:`~oef.core.OEFCoreInterface.send_propose` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :param proposals: either a list of :class:`~oef.schema.Description` or ``bytes``.
        :return: ``None``
        """
        self.agent.send_propose(msg_id, self.id, self.destination, target, proposals)

    def send_accept(self, msg_id: int, target: int) -> None:
        """
        Send an Accept. Analogous to the :func:`~oef.core.OEFCoreInterface.send_accept` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """
        self.agent.send_accept(msg_id, self.id, self.destination, target)

    def send_decline(self, msg_id: int, target: int) -> None:
        """
        Send a Decline. Analogous to the :func:`~oef.core.OEFCoreInterface.send_decline` method.

        :param msg_id: the message identifier for the dialogue.
        :param target: the identifier of the message to whom this message is answering.
        :return: ``None``
        """
        self.agent.send_decline(msg_id, self.id, self.destination, target)


class DialogueAgent(Agent, ABC):
    """
    This class implements a special agent that uses the dialogue to make complex interactions with other agents.
    """

    def __init__(self, oef_proxy: OEFProxy):
        """
        Initialize a Dialogue Agent.

        :param oef_proxy: the proxy to the OEF Node.
        """
        super().__init__(oef_proxy)
        self.dialogues = {}  # type: Dict[DialogueKey, SingleDialogue]

    def register_dialogue(self, dialogue: SingleDialogue) -> None:
        """
        Register a dialogue with another agent.

        :param dialogue: the dialogue to register in the state of the agent.
        :return: ``None``
        :raises ValueError: if the dialogue key is already present.
        """
        dialogue_key = dialogue.key
        if dialogue_key in self.dialogues:
            raise ValueError("Dialogue key {} already in use.".format(dialogue_key))
        self.dialogues[dialogue_key] = dialogue

    def unregister_dialogue(self, dialogue: SingleDialogue) -> None:
        """
        Unregister a dialogue from the state of the agent.

        :param dialogue: the dialogue to unregister.
        :return: ``None``
        :raises ValueError: if the key of the dialogue to be unregistered cannot be found.
        """
        dialogue_key = dialogue.key
        if dialogue_key not in self.dialogues:
            raise ValueError("Dialogue key {} not found.".format(dialogue_key))
        self.dialogues.pop(dialogue_key)

    @abstractmethod
    def on_new_cfp(self, msg_id: int, dialogue_id: int, from_: str, target: int, query: CFP_TYPES) -> None:
        """
        Handle a new :class:`~oef.messages.CFP` message.

        :param msg_id: the message identifier
        :param dialogue_id: the dialogue identifier that the CFP refers to
        :param from_: the id of the agent who sent the CFP.
        :param target: the identifier of the target message
        :param query: the query associated with the CFP.
        :return: ``None``
        """

    @abstractmethod
    def on_new_message(self, msg_id: int, dialogue_id: int, from_: str, content: bytes) -> None:
        """
        Handle a new :class:`~oef.messages.Message` message.

        :param msg_id: the message identifier
        :param dialogue_id: the dialogue id.
        :param from_: the agent id of the source.
        :param content: the content of the message.
        :return: ``None``
        """

    @abstractmethod
    def on_connection_error(self, operation: OEFErrorOperation) -> None:
        """
        Handle a connection error.

        :param operation: the OEF error
        :return: ``None``
        """

    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes):
        try:
            dialogue = self._get_dialogue((origin, dialogue_id))
            dialogue.on_message(msg_id, content)
        except KeyError:
            self.on_new_message(msg_id, dialogue_id, origin, content)

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        try:
            dialogue = self._get_dialogue((origin, dialogue_id))
            dialogue.on_cfp(msg_id, target, query)
        except KeyError:
            self.on_new_cfp(msg_id, dialogue_id, origin, target, query)

    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, proposals: PROPOSE_TYPES):
        dialogue = self._get_dialogue((origin, dialogue_id))
        dialogue.on_propose(msg_id, target, proposals)

    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        dialogue = self._get_dialogue((origin, dialogue_id))
        dialogue.on_accept(msg_id, target)

    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        dialogue = self._get_dialogue((origin, dialogue_id))
        dialogue.on_decline(msg_id, target)

    def _get_dialogue(self, key: DialogueKey) -> SingleDialogue:
        if key not in self.dialogues:
            raise KeyError("Dialogue key {} not found.".format(key))
        return self.dialogues[key]


class GroupDialogues:
    """
    Class to handle a set of dialogues and take decisions taking into accounts all the dialogues.
    """

    def __init__(self, agent: DialogueAgent):
        """
        Instantiate a group of dialogues.

        :param agent: the agent that hold the group of dialogues.
        """
        self.agent = agent
        self.dialogues = {}  # type: Dict[str, SingleDialogue]
        self.best_agent = None  # type: Optional[str]
        self.best_price = 0
        self.nb_answers = 0
        self.first = True

    def add_agents(self, agents: List[SingleDialogue]) -> None:
        """
        Add a list of dialogues to the group.

        :param agents: a list of dialogues.
        :return: ``None``
        """
        for a in agents:
            self.dialogues[a.destination] = a
            self.agent.register_dialogue(a)

    @abstractmethod
    def better(self, price1: int, price2: int) -> bool:
        """
        Determine whether a price is better than another one.

        :param price1: the first price to compare.
        :param price2: the second price to compare
        :return: ``True`` if the first price is better than the second, ``False`` otherwise.
        """

    def update(self, agent: str, price: int) -> None:
        """
        Update the price value received from another agent, e.g. during a negotiation.

        :param agent: the agent who sent us the price.
        :param price: the price sent by the other agent.
        :return: ``None``
        """
        self.nb_answers += 1
        if self.first:
            self.first = False
            self.best_price = price
            self.best_agent = agent
        elif self.better(price, self.best_price):
            self.best_price = price
            self.best_agent = agent
        else:
            pass

        if self.nb_answers >= len(self.dialogues):
            self.finished()

    @abstractmethod
    def finished(self) -> None:
        """
        Handle the end of all the dialogues.

        :return: ``None``
        """
