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
import random
from typing import List, Optional, Tuple, Callable

from oef.agents import Agent
from oef.core import OEFProxy
from oef.dialogue import GroupDialogues, DialogueAgent, SingleDialogue
from oef.messages import CFP_TYPES, OEFErrorOperation, PROPOSE_TYPES
from oef.schema import Description


class SimpleSingleDialogueTest(SingleDialogue):
    """
    A simple specialization of :class:`~oef.dialogue.SingleDialogue`.
    It stores all the messages he receives, so we can track
    the history of the received messages and assert some properties on it.
    """

    def __init__(self, agent: DialogueAgent,
                 destination: str,
                 id_: Optional[int] = None,
                 notify: Callable = None):
        super().__init__(agent, destination, id_)
        self.notify = notify
        self.received_msg = []

    def on_message(self, msg_id: int, content: bytes) -> None:
        self._process_message((msg_id, content))

    def _process_message(self, arguments: Tuple):
        """Store the message into the state of the agent."""
        self.received_msg.append(arguments)

    def on_cfp(self, msg_id: int, target: int, query: CFP_TYPES) -> None:
        self._process_message((msg_id, target, query))

    def on_propose(self, msg_id: int, target: int, proposals: PROPOSE_TYPES):
        self._process_message((msg_id, target, proposals))

    def on_decline(self, msg_id: int, target: int) -> None:
        self._process_message((msg_id, target))

    def on_accept(self, msg_id: int, target: int) -> None:
        self._process_message((msg_id, target))

    def on_dialogue_error(self, answer_id: int, dialogue_id: int, origin: str) -> None:
        pass


class ClientSingleDialogueTest(SimpleSingleDialogueTest):

    def __init__(self, agent: DialogueAgent,
                 destination: str,
                 id_: Optional[int] = None,
                 notify: Callable = None):
        super().__init__(agent, destination, id_)
        self.notify = notify
        self.received_msg = []
        self.agent.send_cfp(1, self.id, destination, 0, None)

    def on_propose(self, msg_id: int, target: int, proposals: PROPOSE_TYPES):
        assert type(proposals) == list and len(proposals) == 1
        proposal = proposals[0]
        self.notify(self.destination, proposal.values["price"])


class GroupDialogueTest(GroupDialogues):

    def __init__(self, agent: DialogueAgent, agents: List[str]):
        super().__init__(agent)

        dialogues = [ClientSingleDialogueTest(agent, a,
                                              notify=lambda from_, price: self.update(from_, price))
                     for a in agents]
        self.add_agents(dialogues)

    def better(self, price1: int, price2: int) -> bool:
        return price1 < price2

    def finished(self) -> None:
        for _, d in self.dialogues.items():
            if d.destination == self.best_agent:
                self.agent.send_accept(2, d.id, d.destination, 1)
            else:
                self.agent.send_decline(2, d.id, d.destination, 1)
        self.agent.stop()


class AgentSingleDialogueTest(DialogueAgent):

    def on_new_cfp(self, msg_id: int, dialogue_id: int, from_: str, target: int, query: CFP_TYPES) -> None:
        self.register_dialogue(SimpleSingleDialogueTest(self, from_, dialogue_id))
        self.on_cfp(msg_id, dialogue_id, from_, target, query)

    def on_new_message(self, msg_id: int, dialogue_id: int, from_: str, content: bytes) -> None:
        self.register_dialogue(SimpleSingleDialogueTest(self, from_, dialogue_id))
        self.on_message(msg_id, dialogue_id, from_, content)

    def on_connection_error(self, operation: OEFErrorOperation) -> None:
        pass


class ClientAgentGroupDialogueTest(DialogueAgent):

    def __init__(self, oef_proxy: OEFProxy):
        super().__init__(oef_proxy)
        self.group = None

    def on_search_result(self, search_id: int, agents: List[str]):
        """For every agent returned in the service search, send a CFP to obtain resources from them."""
        self.group = GroupDialogueTest(self, agents)

    def on_new_cfp(self, from_: str, dialogue_id: int, msg_id: int, target: int, query: CFP_TYPES) -> None:
        pass

    def on_new_message(self, msg_id: int, dialogue_id: int, from_: str, content: bytes) -> None:
        pass

    def on_connection_error(self, operation: OEFErrorOperation) -> None:
        pass


class ServerAgentTest(Agent):

    def __init__(self, oef_proxy: OEFProxy, price: int = random.randint(10, 100)):
        super().__init__(oef_proxy)
        self.price = price

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        proposal = Description({"price": self.price})
        self.send_propose(msg_id + 1, dialogue_id, origin, target + 1, [proposal])

    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        self.stop()

    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        self.stop()

