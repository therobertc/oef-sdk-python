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
Script that clone the oef-core repository and build the oef-core Node.
You must have the oef-core built in order to run tests successfully.
"""
import os
import subprocess
import sys

from git import Repo, RemoteProgress, InvalidGitRepositoryError


def build_project(project_root, build_root, options):
    print('Source.:', project_root)
    print('Build..:', build_root)
    print('Options:')
    for key, value in options.items():
        print(' - {} = {}'.format(key, value))
    print('\n')

    # ensure the build directory exists
    os.makedirs(build_root, exist_ok=True)

    # run cmake
    cmd = ['cmake']
    cmd += [project_root]
    exit_code = subprocess.call(cmd, cwd=build_root)
    if exit_code != 0:
        print('Failed to configure cmake project')
        sys.exit(exit_code)

    # make the project
    if os.path.exists(os.path.join(build_root, "build.ninja")):
        cmd = ["ninja"]
    else:
        cmd = ['make', '-j']
    exit_code = subprocess.call(cmd, cwd=build_root)
    if exit_code != 0:
        print('Failed to make the project')
        sys.exit(exit_code)


def main():

    if not os.path.exists("oef-core"):
        os.system("git clone --recursive https://github.com/fetchai/oef-core.git oef-core")
    else:
        try:
            Repo("oef-core")
        except InvalidGitRepositoryError:
            print("Repository is not valid.")
            exit(1)

    build_project("..", "oef-core/build", {})


if __name__ == '__main__':
    main()
