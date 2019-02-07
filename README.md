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

To run the tests, you need to clone [oef-core](https://github.com/fetchai/oef-core) repository and build the project.
Check that you have installed all the dependencies (see [INSTALL.txt](https://github.com/fetchai/oef-core/blob/master/INSTALL.txt)):

    python scripts/setup_test.py
    
Finally:

    tox -e py3x

Where `x` depends on your Python version (either 3.5, 3.6 or 3.7).

## Documentation

For the documentation we use [Sphinx](http://www.sphinx-doc.org/en/master/).

- Install the required packages with Pipenv and activate the shell:

      pipenv install --dev
      pipenv shell

- Then build the docs with:

      cd docs/
      make html
    
And then just open `index.html` in the `build/html` folder.

