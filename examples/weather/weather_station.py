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
Weather service agent
~~~~~~~~~~~~~~~~~

This script belongs to the ``weather`` example of OEF Agent development, and implements the weather service agent.
It assumes that an instance of the OEF Node is running at ``127.0.0.1:3333``.

The script does the following:

1. Instantiate a ``WeatherStation``
2. Connect and register the agent, as a service, to the OEF Node.
   The service is defined over a specific data model that represents a weather measurement service.
   You can find the definition in the .weather_schema module.
3. Wait for agents interested in the service.


The class ``WeatherStation`` defines the behaviour of the weather service agent. In summary:

* when the agent receives a CFP, it answers with a list of relevant resources, that constitutes his proposal.
  In this example we just answer with only one Description object, that specifies the price of the negotiation.
* on Accept messages, he answers with the available measurements. For the sake of simplicity, they are hard-coded.

"""

from weather_schema import WEATHER_DATA_MODEL
from oef.agents import OEFAgent
from oef.proxy import CFP_TYPES
from oef.schema import Description


class WeatherStation(OEFAgent):
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
    agent = WeatherStation("weather_station", oef_addr="127.0.0.1", oef_port=3333)
    agent.connect()
    agent.register_service(agent.weather_service_description)

    print("Waiting for clients...")
    agent.run()
