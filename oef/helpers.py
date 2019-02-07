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

oef.helpers
~~~~~~~~~~~

This module contains helper functions.

"""

from math import sin, cos, sqrt, asin, radians


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the Haversine distance between two locations (i.e. two pairs of latitude and longitude).

    :param lat1: the latitude of the first location.
    :param lon1: the longitude of the first location.
    :param lat2: the latitude of the second location.
    :param lon2: the longitude of the second location.
    :return: the Haversine distance.
    """

    lat1, lon1, lat2, lon2, = map(radians, [lat1, lon1, lat2, lon2])

    # average earth radius
    R = 6372.8

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    sin_lat_squared = sin(dlat * 0.5) * sin(dlat * 0.5)
    sin_lon_squared = sin(dlon * 0.5) * sin(dlon * 0.5)
    computation = asin(sqrt(sin_lat_squared + sin_lon_squared * cos(lat1) * cos(lat2)))

    d = 2 * R * computation

    return d
