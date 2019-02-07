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
import asyncio
import json
import pprint
from typing import List, Optional, Callable

from oef.proxy import OEFNetworkProxy, OEFProxy

from oef.dialogue import SingleDialogue, DialogueAgent, GroupDialogues
from oef.query import Query, Constraint, Eq

from weather_schema import WEATHER_DATA_MODEL
from oef.schema import Description


from oef.messages import PROPOSE_TYPES, CFP_TYPES, OEFErrorOperation
from oef.agents import Agent, OEFAgent

import random


class WeatherClient(DialogueAgent):
    """Class that implements the behavior of the weather client."""

    def __init__(self, oef_proxy: OEFProxy):
        super().__init__(oef_proxy)
        self.group = None

    def on_search_result(self, search_id: int, agents: List[str]):
        """For every agent returned in the service search, send a CFP to obtain resources from them."""
        print("Agent found: {0}".format(agents))
        self.group = WeatherGroupDialogues(self, agents)

    def on_new_cfp(self, from_: str, dialogue_id: int, msg_id: int, target: int, query: CFP_TYPES) -> None:
        pass

    def on_new_message(self, msg_id: int, dialogue_id: int, from_: str, content: bytes):
        pass

    def on_connection_error(self, operation: OEFErrorOperation) -> None:
        pass


class WeatherClientDialogue(SingleDialogue):

    def __init__(self, agent: DialogueAgent,
                 destination: str,
                 notify: Callable,
                 id_: Optional[int] = None):
        super().__init__(agent, destination, id_)
        self.notify = notify  # type: Callable
        self.data_received = 0
        self.agent.send_cfp(1, self.id, destination, 0, None)

    def on_propose(self, msg_id: int, target: int, proposals: PROPOSE_TYPES):
        print("Received propose from agent {0}".format(self.destination))
        assert type(proposals) == list and len(proposals) == 1
        proposal = proposals[0]
        print("Proposal: {}".format(proposal.values))
        self.notify(self.destination, proposal.values["price"])

    def on_error(self):
        pass

    def on_cfp(self, msg_id: int, target: int, query: CFP_TYPES) -> None:
        pass

    def on_message(self, msg_id: int, content: bytes):
        """Extract and print data from incoming (simple) messages."""

        data = json.loads(content.decode("utf-8"))
        print("[{0}]: Received measurement from {1}: {2}"
              .format(self.agent.public_key, self.destination, pprint.pformat(data)))
        self.agent.stop()

    def on_decline(self, msg_id: int, target: int) -> None:
        pass

    def on_accept(self, msg_id: int, target: int) -> None:
        pass

    def on_dialogue_error(self, answer_id: int, dialogue_id: int, origin: str) -> None:
        pass

    def send_answer(self, winner: str):
        if self.destination == winner:
            print("Sending accept to {}".format(self.destination))
            self.agent.send_accept(2, self.id, self.destination, 1)
        else:
            print("Sending decline to {}".format(self.destination))
            self.agent.send_decline(2, self.id, self.destination, 1)


class WeatherGroupDialogues(GroupDialogues):
    
    def __init__(self, agent: DialogueAgent, agents: List[str]):
        super().__init__(agent)
        dialogues = [WeatherClientDialogue(agent, a,
                                           lambda from_, price: self.update(from_, price))
                     for a in agents]
        self.add_agents(dialogues)
    
    def better(self, price1: int, price2: int) -> bool:
        return price1 < price2

    def finished(self):
        print("Best price: {} from station {}".format(self.best_price, self.best_agent))
        for _, d in self.dialogues.items():
            d.send_answer(self.best_agent)


class WeatherStation(Agent):
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

    def __init__(self, oef_proxy: OEFProxy, price: int):
        super().__init__(oef_proxy)
        self.price = price

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        """Send a simple Propose to the sender of the CFP."""
        print("[{0}]: Received CFP from {1}".format(self.public_key, origin))

        # prepare the proposal with a given price.
        proposal = Description({"price": self.price})
        print("[{}]: Sending propose at price: {}".format(self.public_key, self.price))
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

    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        self.stop()


if __name__ == '__main__':
    # create and connect the agent
    client_proxy = OEFNetworkProxy("weather_client", oef_addr="127.0.0.1", port=3333)
    client = WeatherClient(client_proxy)
    client.connect()

    N = 10
    station_proxies = [OEFNetworkProxy("weather_station_{:02d}".format(i),
                                       oef_addr="127.0.0.1", port=3333) for i in range(N)]

    stations = [WeatherStation(station_proxy, random.randint(10, 50)) for station_proxy in station_proxies]
    for station in stations:
        station.connect()
        station.register_service(0, station.weather_service_description)

    query = Query([
        Constraint("temperature", Eq(True)),
        Constraint("air_pressure", Eq(True)),
        Constraint("humidity", Eq(True))],
        WEATHER_DATA_MODEL)

    client.search_services(0, query)

    asyncio.get_event_loop().run_until_complete(
        asyncio.gather(
            client.async_run(),
            *[station.async_run() for station in stations]
        )
    )


