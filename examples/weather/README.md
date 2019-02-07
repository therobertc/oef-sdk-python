# Weather OEF Agents

## How to run

Check that an instance of [`OEFNode`](https://github.com/fetchai/oef-core) 
is running in your local machine.

Then, run `weather_station.py` script:

    python weather_station.py
    
In another terminal, run:

    python weather_client.py
    
    
## How it works

1. The weather station agent registers to the OEF, and waits for messages.
2. The client send a search result with a query, looking for weather stations
   that provide measurements for temperature, humidity and air pressure.
   Then, he waits for messages.
3. The OEF answers with the services that satisfies the query.
4. The client send a CFP to the service via the OEF Node. The node forwards it to the recipient.
5. The weather station answers with a proposal.
6. The client accept the proposal and notifies the weather station.
7. The station send messages to the client with the desired measurements.

