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

oef.schema
~~~~~~~~~~

This module defines classes to deal with data models and their instances.

"""


import copy
from abc import ABC, abstractmethod
from typing import Union, Type, Optional, List, Dict

import oef.agent_pb2 as agent_pb2
import oef.query_pb2 as query_pb2


class ProtobufSerializable(ABC):
    """
    Interface that includes method for packing/unpacking to/from Protobuf objects.
    """

    @abstractmethod
    def to_pb(self):
        """Convert the object into a Protobuf object"""

    @classmethod
    @abstractmethod
    def from_pb(cls, obj):
        """
        Unpack a Protobuf object.

        :param obj: the Protobuf object to parse.
        :return: an instance of the class that implements the interface.
        """


"""
The allowable types that an Attribute can have
"""
ATTRIBUTE_TYPES = Union[float, str, bool, int]


class AttributeSchema(ProtobufSerializable):
    """
    Description of a single element of datum of either a description or a service.

    This defines the schema that a single entry in a schema must take.

    Examples:

        >>> attr_title    = AttributeSchema("title" ,          str,   True,  "The title of the book.")
        >>> attr_author   = AttributeSchema("author" ,         str,   True,  "The author of the book.")
        >>> attr_genre    = AttributeSchema("genre",           str,   True,  "The genre of the book.")
        >>> attr_year     = AttributeSchema("year",            int,   True,  "The year of publication of the book.")
        >>> attr_avg_rat  = AttributeSchema("average_rating",  float, False, "The average rating of the book.")
        >>> attr_isbn     = AttributeSchema("ISBN",            str,   True,  "The ISBN.")
        >>> attr_ebook    = AttributeSchema("ebook_available", bool,  False, "If the book can be sold as an e-book.")

    """

    """mapping from attribute types to its associated pb"""
    _attribute_type_to_pb = {
        bool: query_pb2.Query.Attribute.BOOL,
        int: query_pb2.Query.Attribute.INT,
        float: query_pb2.Query.Attribute.DOUBLE,
        str: query_pb2.Query.Attribute.STRING,
    }

    def __init__(self,
                 attribute_name: str,
                 attribute_type: Type[ATTRIBUTE_TYPES],
                 is_attribute_required: bool,
                 attribute_description: Optional[str] = None) -> None:
        """
        Initialize an attribute schema.

        :param attribute_name: the name of this attribute.
        :param attribute_type: the type of this attribute, must be a type in ATTRIBUTE_TYPES.
        :param is_attribute_required: does this attribute have to be included.
        :param attribute_description: optional description of this attribute.
        """
        self.name = attribute_name
        self.type = attribute_type
        self.required = is_attribute_required
        self.description = attribute_description

    def to_pb(self) -> query_pb2.Query.Attribute:
        """
        Convert the attribute into a Protobuf object

        :return: the associated Attribute protobuf object.
        """
        attribute = query_pb2.Query.Attribute()
        attribute.name = self.name
        attribute.type = self._attribute_type_to_pb[self.type]
        attribute.required = self.required
        if self.description is not None:
            attribute.description = self.description
        return attribute

    @classmethod
    def from_pb(cls, attribute: query_pb2.Query.Attribute):
        """
        Unpack the attribute Protobuf object.

        :param attribute: the Protobuf object associated with the attribute.
        :return: the attribute.
        """
        return cls(attribute.name,
                   dict(map(reversed, cls._attribute_type_to_pb.items()))[attribute.type],
                   attribute.required,
                   attribute.description if attribute.description else None)

    def __eq__(self, other):
        if type(other) != AttributeSchema:
            return False
        else:
            return self.name == other.name and self.type == other.type and self.required == other.required


class AttributeInconsistencyException(Exception):
    """
    Raised when the attributes in a Description are inconsistent.

    Inconsistency is defined when values do not meet their respective schema, or if the values
    are not of an allowed type.
    """
    pass


class DataModel(ProtobufSerializable):
    """
    This class represents a data model (a.k.a. schema) of the OEFCore.

    Examples:

        >>> book_model = DataModel("book", [
        ...  AttributeSchema("title" ,          str,   True,  "The title of the book."),
        ...  AttributeSchema("author" ,         str,   True,  "The author of the book."),
        ...  AttributeSchema("genre",           str,   True,  "The genre of the book."),
        ...  AttributeSchema("year",            int,   True,  "The year of publication of the book."),
        ...  AttributeSchema("average_rating",  float, False, "The average rating of the book."),
        ...  AttributeSchema("ISBN",            str,   True,  "The ISBN."),
        ...  AttributeSchema("ebook_available", bool,  False, "If the book can be sold as an e-book."),
        ... ], "A data model to describe books.")
    """

    def __init__(self,
                 name: str,
                 attribute_schemas: List[AttributeSchema],
                 description: Optional[str] = None) -> None:
        """
        Initialize a Data Model object.

        :param name: the name of the data model.
        :param attribute_schemas: the list of attributes that constitutes the data model.
        :param description: a short description for the data model.
        """
        self.name = name
        self.attribute_schemas = copy.deepcopy(attribute_schemas)
        self.description = description

    @classmethod
    def from_pb(cls, model: query_pb2.Query.DataModel):
        """
        Unpack the data model Protobuf object.

        :param model: the Protobuf object associated with the data model.
        :return: the data model.
        """

        name = model.name
        attributes = [AttributeSchema.from_pb(attr_pb) for attr_pb in model.attributes]
        description = model.description
        return cls(name, attributes, description)

    def to_pb(self):
        """
        Convert the data model into a Protobuf object

        :return: the associated DataModel Protobuf object.
        """
        model = query_pb2.Query.DataModel()
        model.name = self.name
        model.attributes.extend([attr.to_pb() for attr in self.attribute_schemas])
        if self.description is not None:
            model.description = self.description
        return model

    def __eq__(self, other):
        if type(other) != DataModel:
            return False
        else:
            return self.name == other.name and self.attribute_schemas == other.attribute_schemas


def generate_schema(model_name: str, attribute_values: Dict[str, ATTRIBUTE_TYPES]) -> DataModel:
    """
    Generate a schema that matches the values stored in this description.
    That is, for each attribute (name, value), generate an AttributeSchema.
    It is assumed that each attribute is required.

    :param model_name: the name of the model.
    :param attribute_values: the values of each attribute
    :return: the schema compliant with the values specified.
    """

    return DataModel(model_name, [AttributeSchema(k, type(v), True) for k, v in attribute_values.items()])


class Description(ProtobufSerializable):
    """
    Description of either a service or an agent so it can be understood by the OEF and other agents.

    Contains values of the description, and an optional schema for checking format of values.

    Whenever the description is changed (including when it is create), the attribute values will
    checked to make sure they do not violate the attribute schema.

    Examples:

        >>> It = Description({
        ...     "title" :           "It",
        ...     "author":           "Stephen King",
        ...     "genre":            "horror",
        ...     "year":             1986,
        ...     "average_rating":   4.5,
        ...     "ISBN":             "0-670-81302-8",
        ...     "ebook_available":  True
        ... })

        >>> _1984 = Description({
        ...     "title" :           "1984",
        ...     "author":           "George Orwell",
        ...     "genre":            "novel",
        ...     "year":             1949,
        ...     "ISBN":             "978-0451524935",
        ...     "ebook_available":  False
        ... })
    """

    def __init__(self,
                 attribute_values: Dict[str, ATTRIBUTE_TYPES],
                 data_model: DataModel = None,
                 data_model_name: str = "") -> None:
        """
        Initialize a description.

        :param attribute_values: the values of each attribute in the description. This is a dictionary from
               | attribute name to attribute value, each attribute value must have a type in ATTRIBUTE_TYPES.
        :param data_model: optional schema of this description. If none is provided then the attribute values
               | will not be checked against a schema. Schemas are extremely useful for preventing
               | problems hard to debug, and are highly recommended.
        :param data_model_name: the name of the default data model. If a data model is provided,
               | this paramter is ignored.
        """
        self.values = copy.deepcopy(attribute_values)
        if data_model is not None:
            self.data_model = data_model
            self._check_consistency()
        else:
            self.data_model = generate_schema(data_model_name, attribute_values)

    @staticmethod
    def _extract_value(value: query_pb2.Query.Value) -> ATTRIBUTE_TYPES:
        """
        From a Protobuf query value object to attribute type.

        :param value: an instance of query_pb2.Query.Value.
        :return: the associated attribute type.
        """
        value_case = value.WhichOneof("value")
        if value_case == "s":
            return value.s
        elif value_case == "b":
            return bool(value.b)
        elif value_case == "i":
            return value.i
        elif value_case == "d":
            return value.d

    @classmethod
    def from_pb(cls, query_instance: query_pb2.Query.Instance):
        """
        Unpack the data model Protobuf object.

        :param query_instance: the Protobuf object associated with the data model.
        :return: the data model.
        """
        model = DataModel.from_pb(query_instance.model)
        values = dict([(attr.key, cls._extract_value(attr.value)) for attr in query_instance.values])
        return cls(values, model)

    @staticmethod
    def _to_key_value_pb(key: str, value: ATTRIBUTE_TYPES) -> query_pb2.Query.KeyValue:
        """
        From a (key, attribute value) pair to the associated Protobuf object.

        :param key: the key of the attribute.
        :param value: the value of the attribute.
        :return: the associated Protobuf object.
        """

        kv = query_pb2.Query.KeyValue()
        kv.key = key
        if isinstance(value, bool):
            kv.value.b = value
        elif isinstance(value, int):
            kv.value.i = value
        elif isinstance(value, float):
            kv.value.d = value
        elif isinstance(value, str):
            kv.value.s = value
        return kv

    def to_pb(self) -> query_pb2.Query.Instance:
        """
        Return the description object as a Protobuf query instance.

        :return: the Protobuf query instance object associated to the description.
        """
        instance = query_pb2.Query.Instance()
        instance.model.CopyFrom(self.data_model.to_pb())
        instance.values.extend([self._to_key_value_pb(key, value) for key, value in self.values.items()])
        return instance

    def to_agent_description_pb(self) -> agent_pb2.AgentDescription:
        """
        Convert the description into the Protobuf object associated to the AgentDescription message.

        :return: the associated AgentDescription Protobuf object.
        """
        description = agent_pb2.AgentDescription()
        description.description.CopyFrom(self.to_pb())
        return description

    def _check_consistency(self):
        """
        Checks the consistency of the values of this description.

        If an attribute_schemas has been provided, values are checked against that. If no attribute
        schema has been provided then minimal checking is performed based on the values in the
        provided attribute_value dictionary.

        :raises AttributeInconsistencyException: if values do not meet the schema, or if no schema is present
                                               | if they have disallowed types.
        """
        if self.data_model is not None:
            # check that all required attributes in the schema are contained in
            required_attributes = [s.name for s in self.data_model.attribute_schemas if s.required]
            if not all(a in self.values for a in required_attributes):
                raise AttributeInconsistencyException("Missing required attribute.")

            # check that all values are defined in the schema
            all_schema_attributes = [s.name for s in self.data_model.attribute_schemas]
            if not all(k in all_schema_attributes for k in self.values):
                raise AttributeInconsistencyException("Have extra attribute not in schema")

            # check that each of the values are consistent with that specified in the schema
            for schema in self.data_model.attribute_schemas:
                if schema.name in self.values:
                    if not isinstance(self.values[schema.name], schema.type):
                        # values does not match type in schema
                        raise AttributeInconsistencyException(
                            "Attribute {} has incorrect type".format(schema.name))
                    elif not isinstance(self.values[schema.name], ATTRIBUTE_TYPES.__args__):
                        # value type matches schema, but it is not an allowed type
                        raise AttributeInconsistencyException(
                            "Attribute {} has unallowed type".format(schema.name))

    def __eq__(self, other):
        if type(other) != Description:
            return False
        else:
            return self.values == other.values and self.data_model == other.data_model
