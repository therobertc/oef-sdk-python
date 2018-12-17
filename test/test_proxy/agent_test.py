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


from typing import Tuple, List

from oef import agent_pb2
from oef.agents import Agent
from oef.core import OEFProxy
from oef.messages import CFP_TYPES, PROPOSE_TYPES


class AgentTest(Agent):
    """
    An agent used for tests.
    """

    def __init__(self, proxy: OEFProxy):
        """
        Initialize an Local OEFAgent for tests.
        """
        super().__init__(proxy)
        self.received_msg = []

    def _process_message(self, arguments: Tuple):
        """Add the message to the """
        self.received_msg.append(arguments)

    def on_message(self, origin: str, dialogue_id: int, content: bytes):
        self._process_message((origin, dialogue_id, content))

    def on_search_result(self, search_id: int, agents: List[str]):
        self._process_message((search_id, sorted(agents)))

    def on_cfp(self,
               origin: str,
               dialogue_id: int,
               msg_id: int,
               target: int,
               query: CFP_TYPES):
        self._process_message((origin, dialogue_id, msg_id, target, query))

    def on_propose(self,
                   origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int,
                   proposal: PROPOSE_TYPES):
        self._process_message((origin, dialogue_id, msg_id, target, proposal))

    def on_accept(self,
                  origin: str,
                  dialogue_id: int,
                  msg_id: int,
                  target: int):
        self._process_message((origin, dialogue_id, msg_id, target))

    def on_decline(self,
                   origin: str,
                   dialogue_id: int,
                   msg_id: int,
                   target: int):
        self._process_message((origin, dialogue_id, msg_id, target))

    def on_error(self,
                 operation: agent_pb2.Server.AgentMessage.Error.Operation,
                 dialogue_id: int,
                 message_id: int):
        pass
