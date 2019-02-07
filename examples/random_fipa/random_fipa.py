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
This script simulates a simplified FIPA-based negotiation dialogue, by letting agents make random choices.

There are some simplifications. For instance, every move targets only the previous message, whereas in general
the message can target other opponent's move (still with some restrictions).

You can visualize the resulting sequence diagram by copying and pasting the
output of the script in the Mermaid Live Editor:

https://mermaidjs.github.io/mermaid-live-editor

"""
import asyncio
import random

from oef.agents import OEFAgent
from oef.messages import CFP_TYPES, PROPOSE_TYPES


class Negotiator(OEFAgent):

    def on_cfp(self, msg_id: int,
               dialogue_id: int,
               origin: str,
               target: int,
               query: CFP_TYPES):
        """
        Handle CFP messages. Do the following:

        * with probability 3/4, answer with `Propose`.
        * with probability 1/4, answer with `Decline`, and stop the agent.
        """

        choice = random.random()

        if 0 <= choice < 0.75:
            # send Propose
            print("{}->>{}:Propose()".format(self.public_key, origin))
            self.send_propose(msg_id, dialogue_id, origin, msg_id + 1, b"propose")
        elif 0.75 <= choice <= 1.0:
            # send Decline
            print("{}->>{}:Decline()".format(self.public_key, origin))
            self.send_decline(msg_id, dialogue_id, origin, msg_id + 1)
            self.stop()

    def on_propose(self, msg_id: int,
                   dialogue_id: int,
                   origin: str,
                   target: int,
                   proposal: PROPOSE_TYPES):
        """
        Handle CFP messages. Do the following:

        * with probability 1/2, answer with `Propose`.
        * with probability 1/4, answer with `Accept`, and stop the agent.
        * with probability 1/4, answer with `Decline`, and stop the agent.
        """

        choice = random.random()

        if 0 <= choice < 0.5:
            # send Propose
            print("{}->>{}:Propose()".format(self.public_key, origin))
            self.send_propose(msg_id, dialogue_id, origin, msg_id + 1, b"propose")
        elif 0.5 <= choice < 0.75:
            # send Accept and stop the agent
            print("{}->>{}:Accept()".format(self.public_key, origin))
            self.send_accept(msg_id, dialogue_id, origin, msg_id + 1)
            self.stop()
        elif 0.75 <= choice <= 1.0:
            # send Decline and stop the agent
            print("{}->>{}:Decline()".format(self.public_key, origin))
            self.send_decline(msg_id, dialogue_id, origin, msg_id + 1)
            self.stop()

    def on_accept(self, msg_id: int,
                  dialogue_id: int,
                  origin: str,
                  target: int, ):
        """
        Handle Accept messages. Stop the agent.
        """
        self.stop()

    def on_decline(self, msg_id: int,
                   dialogue_id: int,
                   origin: str,
                   target: int, ):
        """
        Handle Decline messages. Stop the agent.
        """
        self.stop()


if __name__ == '__main__':

    # initialize negotiator agents
    buyer = Negotiator("buyer", oef_addr="127.0.0.1", oef_port=3333)
    seller = Negotiator("seller", oef_addr="127.0.0.1", oef_port=3333)

    # connect to the OEF Node.
    # It assumes there is an OEFNode instance running.
    buyer.connect()
    seller.connect()

    # prints to make `mermaid` sequence diagram.
    print("sequenceDiagram")
    print("{}->>{}:CFP()".format(buyer.public_key, seller.public_key))

    buyer.send_cfp(1, 0, "seller", 0, None)

    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        buyer.async_run(),
        seller.async_run()))
