# OEF Python SDK

![](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue.svg)
![](https://img.shields.io/badge/license-Apache--2.0-lightgrey.svg)

This is the Python SDK for OEF agent development, allowing:

 * registration of agents and services in the OEF
 * searching for agents and services in the OEF
 * constructing a direct communication channel with another agent


## Dependencies

- [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler. You can install it in several  ways, depending on your platform:

  - On Debian-based (e.g. Ubuntu):
        
        sudo apt-get install protobuf-compiler
  - You can do it manually by checking the [release page](https://github.com/protocolbuffers/protobuf/releases) and 
by choosing the release for your platform. The name format is `protoc-$(VERSION)-$(PLATFORM).zip` 
(e.g. for Windows look at `protoc-$(VERSION)-win32.zip`).
  - [Compile from source](https://github.com/protocolbuffers/protobuf/blob/master/src/README.md#c-installation---windows).

    
## Installation
In order to install `oef`, run:

    python setup.py install

## Run the tests

To run the tests, first do: 

    pip install -r requirements.txt
    
Then, you need to clone [oef-core](https://github.com/fetchai/oef-core) repository and build the project:

    python scripts/setup_test.py
    
Finally:

    tox 

## Documentation

For the documentation we use [Sphinx](http://www.sphinx-doc.org/en/master/).

You can build it with:

    cd docs/
    make html
    
And then just open `index.html` in the `build/html` folder.
