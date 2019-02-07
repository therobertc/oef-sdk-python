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
The local counterpart implementation of the weather example.
"""
import asyncio
import json
import pprint
from typing import List

from weather_schema import WEATHER_DATA_MODEL, TEMPERATURE_ATTR, AIR_PRESSURE_ATTR, HUMIDITY_ATTR
from oef.agents import LocalAgent
from oef.proxy import CFP_TYPES, OEFLocalProxy
from oef.proxy import PROPOSE_TYPES
from oef.query import Eq, Constraint
from oef.query import Query
from oef.schema import Description


class WeatherClient(LocalAgent):
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


class WeatherStation(LocalAgent):
    """Class that implements the behaviour of the weather station."""

    weather_service_description = Description(
        {
            "wind_speed": False,
            "temperature": True,
            "air_pressure": True,
            "humidity": True,
        },
        WEATHER_DATA_MODEL
    )

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        """Send a simple Propose to the sender of the CFP."""
        print("[{0}]: Received CFP from {1}".format(self.public_key, origin))

        # prepare the proposal with a given price.
        price = 50
        proposal = Description({"price": price})
        print("[{}]: Sending propose at price: {}".format(self.public_key, price))
        self.send_propose(msg_id + 1, dialogue_id, origin, target + 1, [proposal])

    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        """Once we received an Accept, send the requested data."""
        print("[{0}]: Received accept from {1}."
              .format(self.public_key, origin))

        # send the measurements to the client. for the sake of simplicity, they are hard-coded.
        data = {"temperature": 15.0, "humidity": 0.7, "air_pressure": 1019.0}
        encoded_data = json.dumps(data).encode("utf-8")
        print("[{0}]: Sending data to {1}: {2}".format(self.public_key, origin, pprint.pformat(data)))
        self.send_message(0, dialogue_id, origin, encoded_data)
        self.stop()


if __name__ == "__main__":

    local_node = OEFLocalProxy.LocalNode()

    client = WeatherClient("weather_client", local_node)
    server = WeatherStation("weather_station", local_node)
    client.connect()
    server.connect()

    server.register_service(0, server.weather_service_description)

    query = Query([Constraint(TEMPERATURE_ATTR.name, Eq(True)),
                   Constraint(AIR_PRESSURE_ATTR.name, Eq(True)),
                   Constraint(HUMIDITY_ATTR.name, Eq(True))],
                  WEATHER_DATA_MODEL)

    client.on_search_result(0, ["weather_station"])

    try:
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(local_node.run())
        loop.run_until_complete(asyncio.gather(
            client.async_run(),
            server.async_run()))
        local_node.stop()
    finally:
        local_node.stop()
        client.stop()
        server.stop()
