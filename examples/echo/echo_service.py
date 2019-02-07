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
Echo service agent
~~~~~~~~~~~~~~~~~

This script belongs to the ``echo`` example of OEF Agent development, and implements the echo service agent.
It assumes that an instance of the OEF Node is running at ``127.0.0.1:3333``.

The script does the following:

1. Instantiate a ``EchoServiceAgent``
2. Connect the agent to the OEF Node.
3. Register the agent as an ``echo`` service.
4. Run the agent, waiting for messages from the OEF.


The class ``EchoServiceAgent`` define the behaviour of the echo client agent.

* whenever he receives a message (see ``on_message`` method) from another agent,
he sends back the same message to the origin.

Other methods (e.g. ``on_cfp``, ``on_error`` etc.) are omitted, since not needed.

"""


from oef.agents import OEFAgent
from oef.schema import DataModel, Description, AttributeSchema


# Uncomment the following lines if you want more output
# import logging
# from oef.logger import set_logger
# set_logger("oef", logging.DEBUG)


class EchoServiceAgent(OEFAgent):
    """
    The class that defines the behaviour of the echo service agent.
    """

    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes):
        print("[{}]: Received message: msg_id={}, dialogue_id={}, origin={}, content={}"
              .format(self.public_key, msg_id, dialogue_id, origin, content))
        print("[{}]: Sending {} back to {}".format(self.public_key, content, origin))
        self.send_message(1, dialogue_id, origin, content)


if __name__ == '__main__':

    # create agent and connect it to OEF
    server_agent = EchoServiceAgent("echo_server", oef_addr="127.0.0.1", oef_port=3333)
    server_agent.connect()

    # register a service on the OEF
    echo_feature = AttributeSchema("does_echo", bool, True, "Whether the service agent can do echo or not.")
    echo_model = DataModel("echo", [echo_feature], "echo service.")
    echo_description = Description({"does_echo": True}, echo_model)

    msg_id = 0
    server_agent.register_service(msg_id, echo_description)

    # run the agent
    print("[{}]: Waiting for messages...".format(server_agent.public_key))
    try:
        server_agent.run()
    finally:
        print("[{}]: Disconnecting...".format(server_agent.public_key))
        server_agent.stop()
        server_agent.disconnect()
