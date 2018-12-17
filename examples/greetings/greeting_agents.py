#!/usr/bin/env python3
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
A simple example with OEF Agents that greet each other.
The agents interact via an OEF Node on the network.
"""

import asyncio
from argparse import ArgumentParser
from typing import List
# connect the agents to the OEF
from oef.agents import Agent
from oef.proxy import OEFNetworkProxy
from oef.query import Query
from oef.schema import DataModel, Description

parser = ArgumentParser("greetings-agents", "A simple example with OEF Agents that greet each other.")
parser.add_argument("--addr", default="127.0.0.1", help="IP address of the OEF Node.")
parser.add_argument("--port", default=3333, help="Port for the connection with the OEF Node.")


class GreetingsAgent(Agent):
    """A class that implements the greeting agent."""

    def on_message(self, origin: str, dialogue_id: int, content: bytes):
        print("[{}]: Received message: origin={}, dialogue_id={}, content={}"
              .format(self.public_key, origin, dialogue_id, content))
        if content == b"hello":
            print("[{}]: Sending greetings message to {}".format(self.public_key, origin))
            self.send_message(dialogue_id, origin, b"greetings")

    def on_search_result(self, search_id: int, agents: List[str]):
        if len(agents) > 0:
            print("[{}]: Agents found: {}".format(self.public_key, agents))
            for a in agents:
                self.send_message(0, a, b"hello")
        else:
            print("[{}]: No agent found.".format(self.public_key))


if __name__ == '__main__':

    args = parser.parse_args()

    client_proxy = OEFNetworkProxy("greetings_client", oef_addr=args.addr, port=args.port)
    server_proxy = OEFNetworkProxy("greetings_server", oef_addr=args.addr, port=args.port)

    # create agents
    client_agent = GreetingsAgent(client_proxy)
    server_agent = GreetingsAgent(server_proxy)

    # connect the agents to the OEF
    client_agent.connect()
    server_agent.connect()

    # register the greetings service agent on the OEF
    greetings_model = DataModel("greetings", [], "Greetings service.")
    greetings_description = Description({}, greetings_model)
    server_agent.register_service(greetings_description)

    # the client executes the search for greetings services
    query = Query([], greetings_model)

    print("[{}]: Search for 'greetings' services.".format(client_agent.public_key))
    client_agent.search_services(0, query)

    # run the agents
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            client_agent.async_run(),
            server_agent.async_run()))
    finally:
        client_agent.stop()
        server_agent.stop()
