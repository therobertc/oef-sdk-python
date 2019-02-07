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
    generate_schema, Location

from test.strategies import attribute_schema_values, descriptions, data_models, attributes_schema, locations


def check_inconsistency_checker(schema: List[AttributeSchema], values: Dict[str, ATTRIBUTE_TYPES], exception_string):
    """
    Used to check that that AttributeInconsistencyException is raised with a certain string
    when the two inconsistent schema and values are used to build a Description
    """
    data_model = DataModel("foo", schema, "")
    with pytest.raises(AttributeInconsistencyException, match=exception_string):
        _ = Description(values, data_model)


def generate_schema_checker(name: str, values: Dict[str, ATTRIBUTE_TYPES], expected_schema: DataModel):
    """
    Used to check that generate_schema constructs the expected schema from the provided values
    """
    actual_schema = generate_schema(name, values)

    assert actual_schema == expected_schema


class TestLocation:

    @given(locations())
    def test_serialization(self, location: Location):
        """Test that serialization and deserialization of Location objects work correctly."""
        actual_location = location
        actual_location_pb = actual_location.to_pb()
        expected_location = Location.from_pb(actual_location_pb)

        assert actual_location == expected_location

    @given(locations(), from_type(type))
    def test_eq_different_type(self, location, any):
        """Test that equality test with different types works correctly."""
        assert location != any


class TestAttributeSchema:

    @given(attributes_schema())
    def test_serialization(self, attribute):
        """Test that serialization and deserialization of AttributeSchema objects work correctly."""
        actual_attribute_schema = attribute
        actual_attribute_pb = actual_attribute_schema.to_pb()  # type: query_pb2.Query.Attribute
        expected_attribute_schema = AttributeSchema.from_pb(actual_attribute_pb)
        assert actual_attribute_schema == expected_attribute_schema

    @given(attributes_schema(), from_type(type))
    def test_schema_eq_different_type(self, attribute, any):
        """Test that equality test with different types works correctly."""
        assert attribute != any


class TestDataModel:

    @given(data_models())
    def test_serialization(self, data_model):
        """Test that serialization and deserialization of DataModel objects work correctly."""
        actual_data_model = data_model
        actual_data_model_pb = actual_data_model.to_pb()  # type: query_pb2.Query.DataModel
        expected_data_model= DataModel.from_pb(actual_data_model_pb)
        assert actual_data_model == expected_data_model

    @given(data_models(), from_type(type))
    def test_eq_different_type(self, data_model, any):
        """Test that equality test with different types works correctly."""
        assert data_model != any

    def test_raise_exception_when_duplicated_attribute_name(self):
        """Test that if we try to instantiate a DataModel with a list of attributes with not unique names
        we raise an exception."""
        with pytest.raises(ValueError, match=r"Invalid input value for type.*duplicated attribute name"):
            DataModel("bar", [
                AttributeSchema("foo", bool, True),
                AttributeSchema("foo", str, False)
            ])


class TestDescription:

    @given(descriptions())
    def test_serialization(self, description):
        """Test that serialization and deserialization of Description objects work correctly."""
        actual_description = description
        actual_description_pb = actual_description.to_pb()  # type: query_pb2.Query.DataModel
        expected_description = Description.from_pb(actual_description_pb)
        assert actual_description == expected_description

    @given(descriptions(), from_type(type))
    def test_eq_different_type(self, desc, any):
        """Test that equality test with different types works correctly."""
        assert desc != any


class TestGenerateSchema:

    def test_raise_when_not_required_attribute_is_omitted(self):
        """
        Test that if we miss out a required attribute, we moan about it
        """
        check_inconsistency_checker([AttributeSchema("foo", str, True)], {},
                                    "Missing required attribute.")

    def test_raise_when_have_extra_attribute(self,):
        """
        Test that if we have an attribute that is not in the schema, we moan about it
        """
        check_inconsistency_checker([], {"foo": "bar"}, "extra attribute")

    def test_raise_when_have_incorrect_types(self):
        """
        Test that if an attribute value has a value inconsistent with its schema, we moan.
        """
        check_inconsistency_checker([AttributeSchema("foo", float, True)],
                                    {"foo": "bar"},
                                    "incorrect type")

    def test_raise_when_have_unallowed_types(self):
        """
        Test that if an attribute value has a value inconsistent with its schema, we moan.
        """
        check_inconsistency_checker([AttributeSchema("foo", tuple, True)],
                                    {"foo": tuple()},
                                    "unallowed type")

    def test_raise_when_disallowed_types(self):
        """
        Test that if an attribute has a type that is no in the allowed set, we moan
        """
        check_inconsistency_checker([], {"foo": tuple}, "Have extra attribute not in schema")

    @given(text(), )
    def test_generate_schema_empty(self, name):
        """
        Test that construct_schema constructs the correct schema from empty attribute values
        """
        generate_schema_checker(name, {}, DataModel(name, []))

    @given(text(), text(), attribute_schema_values.map(lambda x: (x, type(x))), one_of(none(), text()))
    def test_generate_schema_single_element(self, schema_name, attribute_name, value_type_pair, description):
        """
        Test that construct_schema constructs the correct schema from single-element attribute values
        """
        value, type_ = value_type_pair
        generate_schema_checker(schema_name, {attribute_name: value},
                                DataModel(schema_name, [AttributeSchema(attribute_name, type_, True, description)]))

    def test_generate_schema_longer_values(self,):
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

