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


"""This module contains Hypothesis strategies for some of the package data types
(e.g. AttributeSchema, DataModel, Description, ...)"""


import typing
from math import isnan
from typing import List

import hypothesis
from hypothesis import assume
from hypothesis.strategies import sampled_from, from_type, composite, text, booleans, one_of, none, lists, tuples

from oef.query import Eq, NotEq, Lt, LtEq, Gt, GtEq, Range, In, NotIn, And, Or, Constraint, Query
from oef.schema import ATTRIBUTE_TYPES, AttributeSchema, DataModel, Description



def _is_attribute_type(t: typing.Type) -> bool:
    """
    Check if a type is a valid attribute schema type.
    :param t: the type.
    :return: True if the type belongs to `ATTRIBUTE_TYPES`, False otherwise.
    """
    return issubclass(t, ATTRIBUTE_TYPES.__args__)


"""Strategy that sample a valid attribute type"""
attribute_schema_types = sampled_from(ATTRIBUTE_TYPES.__args__ + (bool,))

"""Strategy that sample a not valid attribute type."""
not_attribute_schema_types = from_type(type).filter(lambda t: not _is_attribute_type(t))


def is_correct_attribute_value(value: ATTRIBUTE_TYPES):
    if type(value) == int and abs(value) >= 0xFFFFFFFF:
        return False
    if type(value) == float and isnan(value):
        return False

    return True


"""Strategy that sample a value from valid attribute types."""
attribute_schema_values = attribute_schema_types.flatmap(lambda x: from_type(x)).filter(is_correct_attribute_value)


@composite
def value_type_pairs(draw, type_strategy):
    """
    Return a value-type pair.
    """
    type_ = draw(type_strategy)
    value = draw(from_type(type_).filter(is_correct_attribute_value))
    return value, type_


@composite
def attributes_schema(draw) -> AttributeSchema:
    attr_name = draw(text())
    attr_type = draw(attribute_schema_types)
    attr_required = draw(booleans())
    attr_description = draw(text())

    return AttributeSchema(attr_name, attr_type, attr_required, attr_description)


@composite
def data_models(draw):
    data_model_name = draw(text())
    data_model_description = draw(one_of(none(), text()))
    attributes = draw(lists(attributes_schema()))

    data_model = DataModel(data_model_name, attributes, data_model_description)
    return data_model


@composite
def schema_instances(draw, attributes: List[AttributeSchema]):
    if len(attributes) == 0:
        return {}
    else:
        keys, types, required_flags = zip(*[(a.name, a.type, a.required) for a in attributes])
        values = [draw(from_type(type_)) for type_ in types]
        return {k: v for k, v, r in zip(keys, values, required_flags) if r or draw(booleans())}


@composite
def descriptions(draw, from_data_model=False):
    if from_data_model:
        data_model = draw(data_models())
        attributes = data_model.attribute_schemas
    else:
        data_model = None
        attributes = draw(lists(attributes_schema()))
    attributes_values = draw(schema_instances(attributes))

    d = Description(attributes_values, data_model)
    return d


relation_types = sampled_from([Eq, NotEq, Lt, LtEq, Gt, GtEq])


@composite
def relations(draw):
    return draw(relation_types)(draw(attribute_schema_values))


@composite
def ranges(draw):
    value_pairs = draw(sampled_from([str, int, float]).map(lambda x: tuples(from_type(x), from_type(x))))
    value_pair = draw(value_pairs)
    assume(is_correct_attribute_value(value_pair[0]) and is_correct_attribute_value(value_pair[1]))
    return Range(value_pair)


set_types = sampled_from([In, NotIn])


@composite
def query_sets(draw):
    return draw(set_types)(draw(lists(from_type(draw(attribute_schema_types)).filter(is_correct_attribute_value))))


@composite
def and_constraints(draw):
    return And(draw(lists(one_of(relations(), ranges(), query_sets()))))


@composite
def or_constraints(draw):
    return Or(draw(lists(one_of(relations(), ranges(), query_sets()))))


@composite
def constraints(draw):
    return Constraint(draw(attributes_schema()),
                      draw(one_of(relations(), ranges(), query_sets(), and_constraints(), or_constraints())))


@composite
def queries(draw):
    return Query(draw(lists(constraints())),
                 draw(one_of(none(), data_models())))


hypothesis.strategies.register_type_strategy(AttributeSchema, attributes_schema)
hypothesis.strategies.register_type_strategy(DataModel, data_models)
hypothesis.strategies.register_type_strategy(Description, descriptions)
