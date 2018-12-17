# Greetings OEF Agents

## How to run


Check that an instance of [`OEFNode`](https://github.com/fetchai/oef-core) 
is running in your local machine. 
Then, execute the `greeting_agents.py` script:

    python greeting_agents.py
    
Output:

    [greetings_client]: Search for 'greetings' services.
    [greetings_client]: Agents found: ['greetings_server']
    [greetings_server]: Received message: origin=greetings_client, dialogue_id=0, content=b'hello'
    [greetings_server]: Sending greetings message to greetings_client
    [greetings_client]: Received message: origin=greetings_server, dialogue_id=0, content=b'greetings'

There is also a variant of this example that uses a local (non-networked) implementation
of the `OEFNode`:

    python local_greeting_agents.py
    
