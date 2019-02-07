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
import contextlib

from typing import Tuple, List

from oef import agent_pb2
from oef.agents import Agent
from oef.core import OEFProxy
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.proxy import OEFLocalProxy, OEFNetworkProxy
from test.conftest import NetworkOEFNode


class AgentTest(Agent):
    """
    An agent used for tests. The only thing he does is to store all the messages he receives, so
    we can track the history of the received messages and assert some properties on it.
    """

    def __init__(self, proxy: OEFProxy):
        """
        Initialize a OEFAgent for tests.
        """
        super().__init__(proxy)
        self.received_msg = []

    def _process_message(self, arguments: Tuple):
        """Store the message into the state of the agent."""
        self.received_msg.append(arguments)

    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes):
        self._process_message((msg_id, dialogue_id, origin, content))

    def on_search_result(self, search_id: int, agents: List[str]):
        self._process_message((search_id, sorted(agents)))

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES):
        self._process_message((msg_id, dialogue_id, origin, target, query))

    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, proposals: PROPOSE_TYPES):
        self._process_message((msg_id, dialogue_id, origin, target, proposals))

    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        self._process_message((msg_id, dialogue_id, origin, target))

    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int):
        self._process_message((msg_id, dialogue_id, origin, target))

    def on_dialogue_error(self, answer_id: int, dialogue_id: int, origin: str):
        pass

    def on_oef_error(self, answer_id: int, operation: agent_pb2.Server.AgentMessage.OEFError.Operation):
        pass


@contextlib.contextmanager
def setup_local_proxies(n: int, prefix: str) -> List[OEFNetworkProxy]:
    """
    Set up a list of :class:`oef.proxy.OEFLocalProxy`.

    :param n: the number of proxies to set up.
    :param prefix: the prefix to add to the proxies' public keys.
    """
    public_key_prefix = prefix + "-" if prefix else ""
    local_node = OEFLocalProxy.LocalNode()
    proxies = [OEFLocalProxy("{}agent-{}".format(public_key_prefix, i), local_node) for i in range(n)]
    try:
        asyncio.ensure_future(local_node.run())
        yield proxies
    except BaseException:
        raise
    finally:
        local_node.stop()


@contextlib.contextmanager
def setup_network_proxies(n: int, prefix: str) -> List[OEFNetworkProxy]:
    """
    Set up a list of :class:`oef.proxy.OEFNetworkProxy`.

    :param n: the number of proxies to set up.
    :param prefix: the prefix to add to the proxies' public keys.
    """
    public_key_prefix = prefix + "-" if prefix else ""
    proxies = [OEFNetworkProxy("{}agent-{}".format(public_key_prefix, i), "127.0.0.1", 3333) for i in range(n)]
    try:
        with NetworkOEFNode():
            yield proxies
    except BaseException:
        raise


@contextlib.contextmanager
def setup_test_proxies(n: int, local: bool, prefix: str="") -> List[OEFProxy]:
    """
    Set up a list of proxies.

    :param n: the number of proxies to set up.
    :param local: whether the proxies are local (i.e. connecting to a :class:`~oef.proxy.OEFLocalProxy.LocalNode`)
                | or networked.
    :param prefix: the prefix to add to the proxies' public keys.
    :return:
    """
    if local:
        context = setup_local_proxies(n, prefix)
    else:
        context = setup_network_proxies(n, prefix)

    with context as proxies:
        yield proxies


@contextlib.contextmanager
def setup_test_agents(n: int, local: bool, prefix: str="") -> List[AgentTest]:
    with setup_test_proxies(n, local, prefix) as proxies:
        agents = [AgentTest(proxy) for proxy in proxies]
        try:
            yield agents
        except Exception:
            raise
    _stop_agents(agents)


def _stop_agents(agents):
    for a in agents:
        a.stop()

    tasks = asyncio.Task.all_tasks(asyncio.get_event_loop())
    for t in tasks:
        asyncio.get_event_loop().run_until_complete(t)
