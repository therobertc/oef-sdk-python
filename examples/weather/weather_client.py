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
Weather client agent
~~~~~~~~~~~~~~~~~

This script belongs to the ``weather`` example of OEF Agent development, and implements the weather client agent.
It assumes that an instance of the OEF Node is running at ``127.0.0.1:3333``.

The script does the following:

1. Instantiate a ``WeatherClientAgent``
2. Connect the agent to the OEF Node.
3. Make a query on ``echo`` services via the ``search_services`` method.
4. Run the agent, waiting for messages from the OEF.


The class ``WeatherClientAgent`` define the behaviour of the weather client agent. In summary:

* when the agent receives a search result from the OEF (see ``on_search_result``), it sends a CFP to
  every weather station found. This message starts a negotiation with every agent.
  For simplicity, the CFP contains a query with an empty list of constraints, meaning that we do not specify constraints
  on the set of proposals we can receive.
* when the agent receives a Propose message, he will automatically accept the proposal, sending an Accept message.
  Here it is possible to implement multiple strategies, e.g. find the proposal with the minimum
  across different services.
* Then he waits to receive the measurements from the weather station.

It would be nice to extend this example to work with multiple weather stations, and pick the one with the minimum price.


"""
import json
import pprint

from weather_schema import WEATHER_DATA_MODEL, TEMPERATURE_ATTR, AIR_PRESSURE_ATTR, HUMIDITY_ATTR
from oef.agents import OEFAgent

from typing import List
from oef.proxy import PROPOSE_TYPES
from oef.query import Eq, Constraint
from oef.query import Query


class WeatherClient(OEFAgent):
    """Class that implements the behavior of the weather client."""

    def on_search_result(self, search_id: int, agents: List[str]):
        """For every agent returned in the service search, send a CFP to obtain resources from them."""
        if len(agents) == 0:
            print("[{}]: No agent found. Stopping...".format(self.public_key))
            self.stop()
            return

        print("[{0}]: Agent found: {1}".format(self.public_key, agents))
        for agent in agents:
            print("[{0}]: Sending to agent {1}".format(self.public_key, agent))
            # we send a 'None' query, meaning "give me all the resources you can propose."
            query = None
            self.send_cfp(1, 0, agent, 0, query)

    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, proposals: PROPOSE_TYPES):
        """When we receive a Propose message, answer with an Accept."""
        print("[{0}]: Received propose from agent {1}".format(self.public_key, origin))
        for i, p in enumerate(proposals):
            print("[{0}]: Proposal {1}: {2}".format(self.public_key, i, p.values))
        print("[{0}]: Accepting Propose.".format(self.public_key))
        self.send_accept(msg_id, dialogue_id, origin, msg_id + 1)

    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes):
        """Extract and print data from incoming (simple) messages."""
        data = json.loads(content.decode("utf-8"))
        print("[{0}]: Received measurement from {1}: {2}".format(self.public_key, origin, pprint.pformat(data)))
        self.stop()


if __name__ == "__main__":

    # create and connect the agent
    agent = WeatherClient("weather_client", oef_addr="127.0.0.1", oef_port=3333)
    agent.connect()

    # look for service agents registered as 'weather_station' that:
    # - provide measurements for temperature
    # - provide measurements for air pressure
    # - provide measurements for humidity
    query = Query([Constraint(TEMPERATURE_ATTR.name, Eq(True)),
                   Constraint(AIR_PRESSURE_ATTR.name, Eq(True)),
                   Constraint(HUMIDITY_ATTR.name, Eq(True))],
                  WEATHER_DATA_MODEL)

    agent.search_services(0, query)

    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()
