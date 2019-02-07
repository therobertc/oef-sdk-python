# Echo OEF Agents

## How to run

Check that an instance of [`OEFNode`](https://github.com/fetchai/oef-core) 
is running in your local machine.

Then, run `echo_service.py` script:

    python echo_service.py
    
In another terminal, run:

    python echo_client.py
    

## How it works


1. The service agent ``echo_server`` registers itself to the the OEF Node and waits for messages.
2. The ``echo_client`` queries to the OEF Node
3. The OEF Node sends back the list of agents who satisfy
   the query constraints. In this trivial example,
   the only agent returned is the ``echo_server``.
4. The client sends a ``"hello"`` message to the OEF Node,
   which targets the ``echo_server``
5. The OEF Node dispatches the message from ``echo_client`` to ``echo_server``
6. The ``echo_server`` receives the message and sends a new message (with the same content)
   to the OEF Node, which targets the ``echo_client``
7. The OEF Node dispatch the message from ``echo_server`` to ``echo_client``
8. The ``echo_client`` receives the echo message.
