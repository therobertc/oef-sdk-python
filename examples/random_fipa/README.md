# Random FIPA simulator

This script simulates a simplified FIPA-based negotiation dialogue, by letting agents make random choices.

There are some simplifications. For instance, every move targets only the previous message, whereas in general
the message can target other opponent's move (still with some restrictions).

## Run

    python random_fipa.py


The script generates a random [Mermaid](https://mermaidjs.github.io/) 
sequence diagram, like:

    sequenceDiagram
    buyer->>seller:CFP()
    seller->>buyer:Propose()
    buyer->>seller:Propose()
    seller->>buyer:Propose()
    buyer->>seller:Accept()


You can visualize the resulting sequence diagram by copying and pasting the
output of the script in the 
[Mermaid Live Editor](https://mermaidjs.github.io/mermaid-live-editor).
