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
from typing import List

from examples.weather.weather_schema import WEATHER_DATA_MODEL, TEMPERATURE_ATTR, AIR_PRESSURE_ATTR, HUMIDITY_ATTR
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
        print("Agent found: {0}".format(agents))
        for agent in agents:
            print("Sending to agent {0}".format(agent))
            # we send a query with no constraints, meaning "give me all the resources you can propose."
            query = Query([])
            self.send_cfp(0, agent, query)

    def on_propose(self, origin: str, dialogue_id: int, msg_id: int, target: int, proposals: PROPOSE_TYPES):
        """When we receive a Propose message, answer with an Accept."""
        print("Received propose from agent {0}".format(origin))
        for i, p in enumerate(proposals):
            print("Proposal {}: {}".format(i, p.values))
        print("Accepting Propose.")
        self.send_accept(dialogue_id, origin, msg_id + 1, msg_id)

    def on_message(self, origin: str,
                   dialogue_id: int,
                   content: bytes):
        """Extract and print data from incoming (simple) messages."""
        key, value = content.decode().split(":")
        print("Received measurement from {}: {}={}".format(origin, key, float(value)))


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

    def on_cfp(self, origin: str,
               dialogue_id: int,
               msg_id: int,
               target: int,
               query: CFP_TYPES):
        """Send a simple Propose to the sender of the CFP."""
        print("Received CFP from {0}".format(origin))

        # prepare the proposal with a given price.
        proposal = Description({"price": 50})
        self.send_propose(dialogue_id, origin, [proposal], msg_id + 1, target + 1)

    def on_accept(self, origin: str,
                  dialogue_id: int,
                  msg_id: int,
                  target: int):
        """Once we received an Accept, send the requested data."""
        print("Received accept from {0}."
              .format(origin, dialogue_id, msg_id, target))

        # send the measurements to the client. for the sake of simplicity, they are hard-coded.
        self.send_message(dialogue_id, origin, b"temperature:15.0")
        self.send_message(dialogue_id, origin, b"humidity:0.7")
        self.send_message(dialogue_id, origin, b"air_pressure:1019.0")


if __name__ == "__main__":

    local_node = OEFLocalProxy.LocalNode()

    client = WeatherClient("weather_client", local_node)
    server = WeatherStation("weather_station", local_node)
    client.connect()
    server.connect()

    server.register_service(server.weather_service_description)

    query = Query([Constraint(TEMPERATURE_ATTR, Eq(True)),
                   Constraint(AIR_PRESSURE_ATTR, Eq(True)),
                   Constraint(HUMIDITY_ATTR, Eq(True))],
                  WEATHER_DATA_MODEL)

    client.on_search_result(0, ["weather_station"])

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            client.async_run(),
            server.async_run(),
            local_node.run()))
    finally:
        local_node.stop()
        client.stop()
        server.stop()
