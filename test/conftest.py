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
import inspect
import os
import subprocess
import time

from hypothesis import settings

"""The timeout used to test asynchronicity."""
_ASYNCIO_DELAY = 0.1

"""Settings for the Hypothesis package"""
settings(max_examples=100)

ROOT_DIR = ".."
OUR_DIRECTORY = os.path.dirname(inspect.getfile(inspect.currentframe()))
FULL_PATH = [OUR_DIRECTORY, ROOT_DIR, "oef-core", "build", "apps", "node", "OEFNode"]
PATH_TO_NODE_EXEC = os.path.join(*FULL_PATH)


class NetworkOEFNode:

    def __enter__(self):
        FNULL = open(os.devnull, 'w')
        self.p = subprocess.Popen(PATH_TO_NODE_EXEC, stdout=FNULL, stderr=subprocess.STDOUT)
        time.sleep(0.01)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.p.terminate()
        self.p.kill()
