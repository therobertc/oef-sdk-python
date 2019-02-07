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
import json
import pprint

from weather_schema import WEATHER_DATA_MODEL
from oef.agents import OEFAgent
from oef.messages import CFP_TYPES
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


if __name__ == "__main__":
    agent = WeatherStation("weather_station", oef_addr="127.0.0.1", oef_port=3333)
    agent.connect()
    agent.register_service(0, agent.weather_service_description)

    print("[{}]: Waiting for clients...".format(agent.public_key))
    try:
        agent.run()
    finally:
        agent.stop()
        agent.disconnect()
