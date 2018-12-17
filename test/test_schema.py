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

from typing import List, Dict

import pytest
from hypothesis import given
from hypothesis.strategies import text, from_type, one_of, none
from oef import query_pb2

from oef.schema import AttributeSchema, ATTRIBUTE_TYPES, DataModel, AttributeInconsistencyException, Description, \
    generate_schema

from test.hypothesis.strategies import attribute_schema_types, not_attribute_schema_types, \
    value_type_pairs, descriptions, data_models, attributes_schema, attribute_schema_values


def check_inconsistency_checker(schema: List[AttributeSchema], values: Dict[str, ATTRIBUTE_TYPES], exception_string):
    """
    Used to check that that AttributeInconsistencyException is raised with a certain string
    when the two inconsistent schema and values are used to build a Description
    """
    data_model = DataModel("foo", schema, "")
    with pytest.raises(AttributeInconsistencyException, match=exception_string):
        _ = Description(values, data_model)


@given(text(), attribute_schema_types)
def test_raise_when_not_required_attribute_is_omitted(name, attribute_type):
    """
    Test that if we miss out a required attribute, we moan about it
    """
    check_inconsistency_checker([AttributeSchema(name, attribute_type, True)], {},
                                "Missing required attribute.")


def test_raise_when_have_extra_attribute():
    """
    Test that if we have an attribute that is not in the schema, we moan about it
    """
    check_inconsistency_checker([], {"foo": "bar"}, "extra attribute")


def test_raise_when_have_incorrect_types():
    """
    Test that if an attribute value has a value inconsistent with its schema, we moan.
    """
    check_inconsistency_checker([AttributeSchema("foo", float, True)],
                                {"foo": "bar"},
                                "incorrect type")


def test_raise_when_have_unallowed_types():
    """
    Test that if an attribute value has a value inconsistent with its schema, we moan.
    """
    check_inconsistency_checker([AttributeSchema("foo", tuple, True)],
                                {"foo": tuple()},
                                "unallowed type")


@given(text(), not_attribute_schema_types)
def test_raise_when_disallowed_types(name, not_attribute_type):
    """
    Test that if an attribute has a type that is no in the allowed set, we moan
    """
    check_inconsistency_checker([], {name: not_attribute_type}, "Have extra attribute not in schema")


def generate_schema_checker(name: str, values: Dict[str, ATTRIBUTE_TYPES], expected_schema: DataModel):
    """
    Used to check that generate_schema constructs the expected schema from the provided values
    """
    actual_schema = generate_schema(name, values)

    assert actual_schema == expected_schema


@given(text(), )
def test_generate_schema_empty(name):
    """
    Test that construct_schema constructs the correct schema from empty attribute values
    """
    generate_schema_checker(name, {}, DataModel(name, []))


@given(text(), text(), value_type_pairs(attribute_schema_types), one_of(none(), text()))
def test_generate_schema_single_element(schema_name, attribute_name, value_type_pair, description):
    """
    Test that construct_schema constructs the correct schema from single-element attribute values
    """
    value, type_ = value_type_pair
    generate_schema_checker(schema_name, {attribute_name: value},
                            DataModel(schema_name, [AttributeSchema(attribute_name, type_, True, description)]))


def test_generate_schema_longer_values():
    """
    Test that construct_schema constructs the correct schema from longer dict of values
    """
    values = {"foo": "bar",
              "number": 1234,
              "float": 123.4,
              "bool": True}
    schema_attributes = [AttributeSchema("foo", str, True, ""),
                         AttributeSchema("number", int, True, ""),
                         AttributeSchema("float", float, True, ""),
                         AttributeSchema("bool", bool, True, "")]

    generate_schema_checker("foo", values, DataModel("foo", schema_attributes))


@given(value_type_pairs(attribute_schema_types))
def test_description_extract_value(value_type_pair):
    attr_value, attr_type = value_type_pair

    value = query_pb2.Query.Value()
    if attr_type == str:
        value.s = attr_value
    elif attr_type == bool:
        value.b = attr_value
    elif attr_type == int:
        value.i = attr_value
    elif attr_type == float:
        value.d = attr_value

    expected_value = Description._extract_value(value)
    assert type(expected_value) in ATTRIBUTE_TYPES.__args__ + (bool,)
    assert attr_value == expected_value


@given(text(), attribute_schema_values)
def test_description_to_key_value(key: str, value: ATTRIBUTE_TYPES):

    kv = Description._to_key_value_pb(key, value)  # type: query_pb2.Query.KeyValue

    expected_key = kv.key
    if isinstance(value, bool):
        expected_value = kv.value.b
    elif isinstance(value, int):
        expected_value = kv.value.i
    elif isinstance(value, float):
        expected_value = kv.value.d
    elif isinstance(value, str):
        expected_value = kv.value.s
    else:
        raise Exception()

    assert key == expected_key
    assert value == expected_value


@given(attributes_schema())
def test_attribute_schema_to_pb(attribute):
    actual_attribute_schema = attribute
    actual_attribute_pb = actual_attribute_schema.to_pb()  # type: query_pb2.Query.Attribute
    expected_attribute_schema = AttributeSchema.from_pb(actual_attribute_pb)
    assert actual_attribute_schema == expected_attribute_schema


@given(data_models())
def test_data_model_to_pb(data_model):
    actual_data_model= data_model
    actual_data_model_pb = actual_data_model.to_pb()  # type: query_pb2.Query.DataModel
    expected_data_model= DataModel.from_pb(actual_data_model_pb)
    assert actual_data_model == expected_data_model


@given(descriptions(), from_type(type))
def test_description_eq_different_type(desc, any):
    assert desc != any


@given(data_models(), from_type(type))
def test_data_model_eq_different_type(data_model, any):
    assert data_model != any


@given(attributes_schema(), from_type(type))
def test_attribute_schema_eq_different_type(attribute, any):
    assert attribute != any
