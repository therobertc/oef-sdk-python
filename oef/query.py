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

from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Optional

import oef.query_pb2 as query_pb2
from oef.schema import ATTRIBUTE_TYPES, AttributeSchema, DataModel, ProtobufSerializable

RANGE_TYPES = Union[Tuple[str, str], Tuple[int, int], Tuple[float, float]]


class ConstraintType(ProtobufSerializable, ABC):
    """
    This class is used to represent a constraint type.
    """

    @classmethod
    def from_pb(cls, constraint_pb: query_pb2.Query.Constraint.ConstraintType):
        """
        From ConstraintType protobuf to a ConstraintType.
        It returns an instance of one of the following:

        * :class:`~oef.query.Relation`
        * :class:`~oef.query.Set`
        * :class:`~oef.query.Range`
        * :class:`~oef.query.And`
        * :class:`~oef.query.Or`

        :param constraint_pb: the constraint protobuf object
        :return: the associated ``ConstraintType`` instance.
        """
        constraint_case = constraint_pb.WhichOneof("constraint")
        if constraint_case == "relation":
            return Relation.from_pb(constraint_pb.relation)
        elif constraint_case == "set_":
            return Set.from_pb(constraint_pb.set_)
        elif constraint_case == "range_":
            return Range.from_pb(constraint_pb.range_)
        elif constraint_case == "and_":
            return And.from_pb(constraint_pb.and_)
        elif constraint_case == "or_":
            return Or.from_pb(constraint_pb.or_)


class Relation(ConstraintType, ABC):
    """
    A constraint type that allows you to impose specific values
    for the attributes.

    The specific operator of the relation is defined in the
    subclasses that extend this class.
    """

    def __init__(self, value: ATTRIBUTE_TYPES) -> None:
        """
        Initialize a Relation object.

        :param value: the right value of the relation.
        """
        self.value = value

    @property
    @abstractmethod
    def operator(self) -> query_pb2.Query.Relation:
        """The operator of the relation."""

    @classmethod
    def from_pb(cls, relation: query_pb2.Query.Relation):
        """
        From the Relation Protobuf object to the associated
        instance of a subclass of Relation.

        :param relation: the Protobuf object that represents the relation constraint.
        :return: an instance of one of the subclasses of Relation.
        """

        relations_from_pb = {
            query_pb2.Query.Relation.GTEQ: GtEq,
            query_pb2.Query.Relation.GT: Gt,
            query_pb2.Query.Relation.LTEQ: LtEq,
            query_pb2.Query.Relation.LT: Lt,
            query_pb2.Query.Relation.NOTEQ: NotEq,
            query_pb2.Query.Relation.EQ: Eq
        }

        relation_class = relations_from_pb[relation.op]
        value_case = relation.val.WhichOneof("value")
        if value_case == "s":
            return relation_class(relation.val.s)
        elif value_case == "b":
            return relation_class(relation.val.b)
        elif value_case == "i":
            return relation_class(relation.val.i)
        elif value_case == "d":
            return relation_class(relation.val.d)

    def to_pb(self) -> query_pb2.Query.Constraint.ConstraintType:
        """
        From an instance of Relation to its associated Protobuf object.

        :return: the ConstraintType Protobuf object that contains the relation.
        """
        relation = query_pb2.Query.Relation()
        relation.op = self.operator()
        query_value = query_pb2.Query.Value()
        if isinstance(self.value, bool):
            query_value.b = self.value
        elif isinstance(self.value, int):
            query_value.i = self.value
        elif isinstance(self.value, float):
            query_value.d = self.value
        elif isinstance(self.value, str):
            query_value.s = self.value
        relation.val.CopyFrom(query_value)
        constraint_type = query_pb2.Query.Constraint.ConstraintType()
        constraint_type.relation.CopyFrom(relation)
        return constraint_type

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        else:
            return self.value == other.value


class Eq(Relation):
    """
    The equality relation.

    Examples:
        >>> # all the books whose author is Stephen King
        >>> c = Constraint(AttributeSchema("author", str, True),  Eq("Stephen King"))
    """

    def operator(self):
        return query_pb2.Query.Relation.EQ


class NotEq(Relation):
    """
    The non-equality relation.

    Examples:
        >>> # all the books that are not of the genre Horror
        >>> c = Constraint(AttributeSchema("genre", str, True),   NotEq("horror"))
    """

    def operator(self):
        return query_pb2.Query.Relation.NOTEQ


class Lt(Relation):
    """Less-than relation.

    Examples:
        >>> # all the books published before 1990
        >>> c = Constraint(AttributeSchema("year", int, True), Lt(1990))
    """

    def operator(self):
        return query_pb2.Query.Relation.LT


class LtEq(Relation):
    """
    Less-than-equal relation.

    Examples:
        >>> # all the books published before 1990, 1990 included
        >>> c = Constraint(AttributeSchema("year", int, True), LtEq(1990))
    """

    def operator(self):
        return query_pb2.Query.Relation.LTEQ


class Gt(Relation):
    """
    Greater-than relation.

    Examples:
        >>> # all the books with rating greater than 4.0
        >>> c = Constraint(AttributeSchema("average_rating", float, True), Gt(4.0))
    """

    def operator(self):
        return query_pb2.Query.Relation.GT


class GtEq(Relation):
    """
    Greater-than-equal relation.

    Examples:
        >>> # all the books published after 2000, included
        >>> c = Constraint(AttributeSchema("year", int, True), GtEq(2000))
    """

    def operator(self):
        return query_pb2.Query.Relation.GTEQ


class Range(ConstraintType):
    """
    A constraint type that allows you to restrict the values of the attribute in a given range.
    """

    def __init__(self, values: RANGE_TYPES) -> None:
        """
        Initialize a range constraint type.

        :param values: a pair of ``int``, a pair of ``str``, or a pair of ``float`.
        """
        self.values = values

    def to_pb(self) -> query_pb2.Query.Constraint.ConstraintType:
        """
        From an instance of Range to its associated Protobuf object.

        :return: the ConstraintType Protobuf object that contains the range.
        """
        range_ = query_pb2.Query.Range()
        if isinstance(self.values[0], str):
            values = query_pb2.Query.StringPair()
            values.first = self.values[0]
            values.second = self.values[1]
            range_.s.CopyFrom(values)
        elif isinstance(self.values[0], int):
            values = query_pb2.Query.IntPair()
            values.first = self.values[0]
            values.second = self.values[1]
            range_.i.CopyFrom(values)
        elif isinstance(self.values[0], float):
            values = query_pb2.Query.DoublePair()
            values.first = self.values[0]
            values.second = self.values[1]
            range_.d.CopyFrom(values)
        constraint_type = query_pb2.Query.Constraint.ConstraintType()
        constraint_type.range_.CopyFrom(range_)
        return constraint_type

    @classmethod
    def from_pb(cls, range_pb: query_pb2.Query.Range):
        """
        From the Range Protobuf object to the associated instance of ``Range``.

        :param range_pb: the Protobuf object that represents the range.
        :return: an instance of ``Range`` equivalent to the Protobuf object provided as input.
        """

        range_case = range_pb.WhichOneof("pair")
        if range_case == "s":
            return cls((range_pb.s.first, range_pb.s.second))
        elif range_case == "i":
            return cls((range_pb.i.first, range_pb.i.second))
        elif range_case == "d":
            return cls((range_pb.d.first, range_pb.d.second))

    def __eq__(self, other):
        if type(other) != Range:
            return False
        else:
            return self.values == other.values


SET_TYPES = Union[List[float], List[str], List[bool], List[int]]


class Set(ConstraintType, ABC):
    """
    A constraint type that allows you to restrict the values of the attribute in a specific set.

    The specific operator of the relation is defined in the subclasses that extend this class.
    """

    def __init__(self, values: SET_TYPES) -> None:
        """
        Initialize a Set constraint.

        :param values: a list of values for the set relation.
        """
        self.values = values

    @property
    @abstractmethod
    def operator(self) -> query_pb2.Query.Set:
        """The operator over the set."""

    def to_pb(self):
        """
        From an instance of one of the subclasses of Set to its associated Protobuf object.

        :return: the ConstraintType Protobuf object that contains the set constraint.
        """
        set_ = query_pb2.Query.Set()
        set_.op = self.operator()

        value_type = type(self.values[0]) if len(self.values) > 0 else str

        if value_type == str:
            values = query_pb2.Query.Set.Values.Strings()
            values.vals.extend(self.values)
            set_.vals.s.CopyFrom(values)
        elif value_type == bool:
            values = query_pb2.Query.Set.Values.Bools()
            values.vals.extend(self.values)
            set_.vals.b.CopyFrom(values)
        elif value_type == int:
            values = query_pb2.Query.Set.Values.Ints()
            values.vals.extend(self.values)
            set_.vals.i.CopyFrom(values)
        elif value_type == float:
            values = query_pb2.Query.Set.Values.Doubles()
            values.vals.extend(self.values)
            set_.vals.d.CopyFrom(values)

        constraint_type = query_pb2.Query.Constraint.ConstraintType()
        constraint_type.set_.CopyFrom(set_)
        return constraint_type

    @classmethod
    def from_pb(cls, set_pb: query_pb2.Query.Set):
        """
        From the Set Protobuf object to the associated
        instance of a subclass of Set.

        :param set_pb: the Protobuf object that represents the set constraint.
        :return: the object of one of the subclasses of ``Set``.
        """
        op_from_pb = {
            query_pb2.Query.Set.IN: In,
            query_pb2.Query.Set.NOTIN: NotIn
        }
        set_class = op_from_pb[set_pb.op]
        value_case = set_pb.vals.WhichOneof("values")
        if value_case == "s":
            return set_class(set_pb.vals.s.vals)
        elif value_case == "b":
            return set_class(set_pb.vals.b.vals)
        elif value_case == "i":
            return set_class(set_pb.vals.i.vals)
        elif value_case == "d":
            return set_class(set_pb.vals.d.vals)

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.values == other.values


class In(Set):
    """
    Class that implements the 'in set' constraint type.
    That is, the value of attribute over which the constraint is defined
    must be in the set of values provided.

    Examples:

        >>> # all the books whose genre is one of `Horror`, `Science fiction`, `Non-fiction`
        >>> c = Constraint(AttributeSchema("genre", str, True), In(["horror", "science fiction", "non-fiction"]))

    """

    def __init__(self, values: SET_TYPES):
        super().__init__(values)

    def operator(self):
        return query_pb2.Query.Set.IN


class NotIn(Set):
    """
    Class that implements the 'not in set' constraint type.
    That is, the value of attribute over which the constraint is defined
    must be not in the set of values provided.

    Examples:

        >>> # all the books that have not been published neither in 1990, nor in 1995, nor in 2000
        >>> c = Constraint(AttributeSchema("year", int, True), NotIn([1990, 1995, 2000]))

    """

    def __init__(self, values: SET_TYPES):
        super().__init__(values)

    def operator(self):
        return query_pb2.Query.Set.NOTIN


class And(ConstraintType):
    """
    A constraint type that allows you to specify a conjunction of constraints over an attribute.
    That is, the ``And`` constraint is satisfied whenever all the constraints that constitute the and are satisfied.

    Examples:

        >>> # all the books whose title is between 'I' and 'J' (alphanumeric order) but not equal to 'It'
        >>> c = Constraint(AttributeSchema("title", str, True),   And([Range(("I", "J")), NotEq("It")]))

    """
    def __init__(self, constraints: List[ConstraintType]) -> None:
        """
        Initialize an ``And`` constraint.

        :param constraints: the list of constraints to be interpreted in conjunction.
        """
        self.constraints = constraints

    def to_pb(self):
        """
        From an instance of ``And`` to its associated Protobuf object.

        :return: the ConstraintType Protobuf object that contains the ``And`` constraint.
        """
        and_pb = query_pb2.Query.Constraint.ConstraintType.And()
        and_pb.expr.extend([constraint.to_pb() for constraint in self.constraints])
        constraint_type = query_pb2.Query.Constraint.ConstraintType()
        constraint_type.and_.CopyFrom(and_pb)
        return constraint_type

    @classmethod
    def from_pb(cls, constraint_pb: query_pb2.Query.Constraint.ConstraintType.And):
        """
        From the And Protobuf object to the associated instance of ``And``.

        :param constraint_pb: the Protobuf object that represents the ``And`` constraint.
        :return: an instance of ``And`` equivalent to the Protobuf object.
        """

        expr = [ConstraintType.from_pb(c) for c in constraint_pb.expr]
        return cls(expr)

    def __eq__(self, other):
        if type(other) != And:
            return False
        else:
            return self.constraints == other.constraints


class Or(ConstraintType):
    """
    A constraint type that allows you to specify a disjunction of constraints.
    That is, the Or constraint is satisfied whenever at least one of the constraints
    that constitute the or is satisfied.

    Examples:

        >>> # all the books that have been published either before the year 1960 or after the year 1970
        >>> c = Constraint(AttributeSchema("year", int, True),   Or([Lt(1960), Gt(1970)]))

    """

    def __init__(self, constraints: List[ConstraintType]) -> None:
        """
        Initialize an ``Or`` constraint.

        :param constraints: the list of constraints to be interpreted in disjunction.
        """
        self.constraints = constraints

    def to_pb(self):
        """
        From an instance of ``Or`` to its associated Protobuf object.

        :return: the ConstraintType Protobuf object that contains the ``Or`` constraint.
        """

        or_pb = query_pb2.Query.Constraint.ConstraintType.Or()
        or_pb.expr.extend([constraint.to_pb() for constraint in self.constraints])
        constraint_type = query_pb2.Query.Constraint.ConstraintType()
        constraint_type.or_.CopyFrom(or_pb)
        return constraint_type

    @classmethod
    def from_pb(cls, constraint_pb: query_pb2.Query.Constraint.ConstraintType.Or):
        """
        From the ``Or`` Protobuf object to the associated instance of Or.

        :param constraint_pb: the Protobuf object that represents the ``Or`` constraint.
        :return: an instance of ``Or`` equivalent to the Protobuf object.
        """
        expr = [ConstraintType.from_pb(c) for c in constraint_pb.expr]
        return cls(expr)

    def __eq__(self, other):
        if type(other) != Or:
            return False
        else:
            return self.constraints == other.constraints


class Constraint(ProtobufSerializable):
    """
    A class that represent a constraint over an attribute.
    """

    def __init__(self,
                 attribute: AttributeSchema,
                 constraint: ConstraintType) -> None:
        self.attribute = attribute
        self.constraint = constraint

    def to_pb(self):
        """
        Return the associated Protobuf object.

        :return: a Protobuf object equivalent to the caller object.
        """
        constraint = query_pb2.Query.Constraint()
        constraint.attribute.CopyFrom(self.attribute.to_pb())
        constraint.constraint.CopyFrom(self.constraint.to_pb())
        return constraint

    @classmethod
    def from_pb(cls, constraint_pb: query_pb2.Query.Constraint):
        """
        From the ``Constraint`` Protobuf object to the associated instance of ``Constraint``.

        :param constraint_pb: the Protobuf object that represents the ``Constraint`` object.
        :return: an instance of ``Constraint`` equivalent to the Protobuf object provided in input.
        """
        constraint_type = ConstraintType.from_pb(constraint_pb.constraint)
        return cls(AttributeSchema.from_pb(constraint_pb.attribute), constraint_type)

    def __eq__(self, other):
        if type(other) != Constraint:
            return False
        else:
            return self.attribute == other.attribute and self.constraint == other.constraint


class Query(ProtobufSerializable):
    """
    Representation of a search that is to be performed. Currently a search is represented as a
    set of key value pairs that must be contained in the description of the service/ agent.

    Examples:

        >>> # return all the books written by Stephen King published after 1990, and available as an e-book:
        >>> attr_author   = AttributeSchema("author" ,         str,   True,  "The author of the book.")
        >>> attr_year     = AttributeSchema("year",            int,   True,  "The year of publication of the book.")
        >>> attr_ebook    = AttributeSchema("ebook_available", bool,  False, "If the book can be sold as an e-book.")
        >>> q = Query([
        ...     Constraint(attr_author, Eq("Stephen King")),
        ...     Constraint(attr_year, Gt(1990)),
        ...     Constraint(attr_ebook, Eq(True))
        ... ])
    """

    def __init__(self,
                 constraints: List[Constraint],
                 model: Optional[DataModel] = None) -> None:
        """
        Initialize a query.

        :param constraints: a list of ``Constraint``.
        :param model: the data model where the query is defined.
        """
        self.constraints = constraints
        self.model = model

    def to_pb(self) -> query_pb2.Query.Model:
        """
        Return the associated Protobuf object.

        :return: a Protobuf object equivalent to the caller object.
        """
        query = query_pb2.Query.Model()
        query.constraints.extend([constraint.to_pb() for constraint in self.constraints])
        if self.model is not None:
            query.model.CopyFrom(self.model.to_pb())
        return query

    @classmethod
    def from_pb(cls, query: query_pb2.Query.Model):
        """
        From the ``Query`` Protobuf object to the associated instance of ``Query``.

        :param query: the Protobuf object that represents the ``Query`` object.
        :return: an instance of ``Query`` equivalent to the Protobuf object provided in input.
        """
        constraints = [Constraint.from_pb(constraint_pb) for constraint_pb in query.constraints]
        return cls(constraints, DataModel.from_pb(query.model) if query.HasField("model") else None)

    def __eq__(self, other):
        if type(other) != Query:
            return False
        return self.constraints == other.constraints and self.model == other.model
