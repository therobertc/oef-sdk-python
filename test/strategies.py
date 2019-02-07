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


"""This module contains Hypothesis strategies for some of the data types
(e.g. AttributeSchema, DataModel, Description, ...)"""


from typing import List, Optional, Type

import hypothesis
from hypothesis.strategies import integers, sampled_from, composite, text, booleans, one_of, none, lists, tuples,\
                                  floats, register_type_strategy

from oef.query import Eq, NotEq, Lt, LtEq, Gt, GtEq, Range, In, NotIn, And, Or, Constraint, Query, Not, Distance
from oef.schema import AttributeSchema, DataModel, Description, Location, ATTRIBUTE_TYPES

integers_32 = integers(min_value=-2**32 + 1, max_value=2**32 - 1)
floats_no_nan = floats(allow_nan=False)


@composite
def locations(draw):
    latitude = draw(floats(min_value=-90.0, max_value=90.0))
    longitude = draw(floats(min_value=-180.0, max_value=180.0))
    return Location(latitude, longitude)


register_type_strategy(Location, locations())

strategies_by_type = {
    int: integers_32,
    float: floats_no_nan,
    bool: booleans(),
    str: text(),
    Location: locations()
}

attribute_schema_types = sampled_from(ATTRIBUTE_TYPES.__args__ + (bool, ))
attribute_schema_values = one_of(integers_32, floats_no_nan, text(), booleans(), locations())
ordered_values = one_of(integers_32, floats_no_nan, text())
set_values = one_of(lists(integers_32),
                    lists(floats_no_nan),
                    lists(text()),
                    lists(booleans()),
                    lists(locations))
range_values = one_of(*[tuples(integers_32, integers_32),
                        tuples(floats_no_nan, floats_no_nan),
                        tuples(text(), text()),
                        tuples(locations(), locations())])

@composite
def attributes_schema(draw):
    attr_name = draw(text())
    attr_type = draw(attribute_schema_types)
    attr_required = draw(booleans())
    attr_description = draw(text())

    return AttributeSchema(attr_name, attr_type, attr_required, attr_description)


@composite
def data_models(draw, min_size=0):
    data_model_name = draw(text())
    data_model_description = draw(one_of(none(), text()))

    # data model must have attributes with unique names
    attributes = draw(lists(attributes_schema(), unique_by=lambda x: x.name, min_size=min_size, max_size=3))

    data_model = DataModel(data_model_name, attributes, data_model_description)
    return data_model


@composite
def schema_instances(draw, attributes: List[AttributeSchema]):
    if len(attributes) == 0:
        return {}
    else:
        keys, types, required_flags = zip(*[(a.name, a.type, a.required) for a in attributes])
        values = [draw(strategies_by_type[type_]) for type_ in types]
        return {k: v for k, v, r in zip(keys, values, required_flags) if r or draw(booleans())}


@composite
def descriptions(draw, from_data_model=False):

    if from_data_model:
        data_model = draw(data_models())
        attributes = data_model.attribute_schemas
    else:
        data_model = None
        attributes = draw(lists(attributes_schema(), max_size=3))
    attributes_values = draw(schema_instances(attributes))

    d = Description(attributes_values, data_model)
    return d


relation_types = sampled_from([Eq, NotEq, Lt, LtEq, Gt, GtEq])
ordered_relation_types = sampled_from([Lt, LtEq, Gt, GtEq])
equality_relation_types = sampled_from([Eq, NotEq])


@composite
def ordered_relations(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    if type_:
        return draw(ordered_relation_types)(draw(strategies_by_type[type_]))
    else:
        return draw(ordered_relation_types)(draw(ordered_values))


@composite
def equality_relations(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    if type_:
        return draw(equality_relation_types)(draw(strategies_by_type[type_]))
    else:
        return draw(equality_relation_types)(draw(attribute_schema_values))


@composite
def relations(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    return draw(one_of(ordered_relations(type_), equality_relations(type_)))


@composite
def ranges(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    if type_:
        type_strategy = strategies_by_type[type_]
        return Range(draw(tuples(type_strategy, type_strategy)))
    else:
        return Range(draw(range_values))


set_types = sampled_from([In, NotIn])


@composite
def query_sets(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    if type_:
        return draw(set_types)(draw(lists(strategies_by_type[type_], max_size=3)))
    else:
        return draw(set_types)(draw(lists(strategies_by_type[draw(attribute_schema_types)], max_size=3)))


@composite
def distances(draw, type_: Type[ATTRIBUTE_TYPES] = None):
    return Distance(draw(locations()), draw(floats(min_value=0.0, allow_nan=False)))


type_to_compatible_constraint_types = {
    int:      [equality_relations, ordered_relations, ranges, query_sets],
    str:      [equality_relations, ordered_relations, ranges, query_sets],
    bool:     [equality_relations, query_sets],
    float:    [equality_relations, ordered_relations, ranges, query_sets],
    Location: [equality_relations, ranges, query_sets, distances],
}


@composite
def constraint_expressions(draw, attributes: Optional[List[AttributeSchema]] = None):
    return draw(one_of(constraints(attributes),
                       and_constraints(attributes),
                       or_constraints(attributes),
                       not_constraints(attributes)))


@composite
def _constraints_from_attributes(draw, attributes: List[AttributeSchema]):
    attribute = draw(sampled_from(attributes))
    attributes_name = attribute.name
    attribute_type = attribute.type

    compatible_constraint_types = type_to_compatible_constraint_types[attribute_type]
    constraint_type_strategy = draw(sampled_from(compatible_constraint_types))
    return Constraint(attributes_name,
                      draw(constraint_type_strategy(type_=attribute_type)))


@composite
def constraints(draw, attributes: Optional[List[AttributeSchema]] = None):
    """
    Generate ``Constraint`` objects. Optionally, you can specify a list of desired attribute names.
    """
    if attributes is None:
        return Constraint(draw(text()),
                          draw(one_of(relations(),
                                      ranges(),
                                      query_sets(),
                                      distances())))
    else:
        return draw(_constraints_from_attributes(attributes))


@composite
def and_constraints(draw, attributes: Optional[List[AttributeSchema]] = None):
    return And(draw(lists(constraints(attributes), min_size=2, max_size=3)))


@composite
def or_constraints(draw, attributes: Optional[List[AttributeSchema]] = None):
    return Or(draw(lists(constraints(attributes), min_size=2, max_size=3)))


@composite
def not_constraints(draw, attributes: Optional[List[AttributeSchema]] = None):
    return Not(draw(constraints(attributes)))


@composite
def queries(draw):
    # a proper data model for a valid query is either None or a non-empty Data Model (hence min_size=1)
    data_model = draw(one_of(none(), data_models(min_size=1)))

    # if the data model is not None:
    if data_model:
        # generate constraints from attributes name
        attributes = data_model.attribute_schemas
    else:
        attributes = None

    return Query(draw(lists(constraint_expressions(attributes), min_size=1, max_size=3)), data_model)


hypothesis.strategies.register_type_strategy(AttributeSchema, attributes_schema)
hypothesis.strategies.register_type_strategy(DataModel, data_models)
hypothesis.strategies.register_type_strategy(Description, descriptions)
