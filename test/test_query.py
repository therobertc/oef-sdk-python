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
import pytest
from hypothesis import given

from oef import query_pb2
from oef.query import Relation, Range, Set, And, Or, Constraint, Query, Eq, In, Not, Distance
from oef.schema import Location, DataModel, AttributeSchema
from test.strategies import relations, ranges, query_sets, and_constraints, or_constraints, constraints, \
    queries, not_constraints, distances


class TestRelation:

    @given(relations())
    def test_serialization(self, relation: Relation):
        """Test that serialization and deserialization of ``Relation`` objects work correctly."""

        expected_relation = relation
        relation_pb = expected_relation.to_pb()  # type: query_pb2.Query.Relation
        actual_relation = Relation.from_pb(relation_pb)

        assert expected_relation == actual_relation

    def test_not_equal_when_compared_with_different_type(self):
        a_relation = Eq("foo")
        not_a_relation = tuple()

        assert a_relation != not_a_relation


class TestRange:

    @given(ranges())
    def test_serialization(self, range_: Range):
        """Test that serialization and deserialization of ``Range`` objects work correctly."""

        expected_range = range_
        range_pb = expected_range.to_pb()  # type: query_pb2.Query.Relation
        actual_range = Range.from_pb(range_pb)

        assert expected_range == actual_range

    def test_not_equal_when_compared_with_different_type(self):
        a_range = Range(("foo", "bar"))
        not_a_range = tuple()

        assert a_range != not_a_range


class TestSet:

    @given(query_sets())
    def test_serialization(self, set_: Set):
        """Test that serialization and deserialization of ``Set`` objects work correctly."""
        expected_set = set_
        set_pb = expected_set.to_pb()
        actual_set = Set.from_pb(set_pb)

        assert expected_set == actual_set

    def test_not_equal_when_compared_with_different_type(self):
        a_set = In(["foo", "bar"])
        not_a_set = tuple()

        assert a_set != not_a_set


class TestDistance:

    @given(distances())
    def test_serialization(self, distance):
        """Test that serialization and deserialization of ``Distance`` objects work correctly."""
        expected_distance = distance
        distance_pb = distance.to_pb()
        actual_distance = Distance.from_pb(distance_pb)
        
        assert expected_distance == actual_distance

    def test_not_equal_when_compared_with_different_type(self):
        a_distance = Distance(Location(45.0, 45.0), 1.0)
        not_a_distance = tuple()

        assert a_distance != not_a_distance


class TestConstraint:

    @given(constraints())
    def test_serialization(self, constraint: Constraint):
        """Test that serialization and deserialization of ``Constraint`` objects work correctly."""
        expected_constraint = constraint
        constraint_pb = constraint.to_pb()
        actual_constraint = Constraint.from_pb(constraint_pb)

        assert expected_constraint == actual_constraint

    def test_not_equal_when_compared_with_different_type(self):
        a_constraint = Constraint("foo", In([]))
        not_a_constraint = tuple()

        assert a_constraint != not_a_constraint

    def test_raise_exception_when_not_supported_constrainttype(self):
        with pytest.raises(ValueError, match="The constraint type is not valid"):
            a_constraint = Constraint("foo", tuple())
            a_constraint.to_pb()


class TestAnd:

    @given(and_constraints())
    def test_serialization(self, and_: And):
        """Test that serialization and deserialization of ``And`` objects work correctly."""

        expected_and = and_
        and_pb = and_.to_pb()  # type: query_pb2.Query.ConstraintExpr.And
        actual_and = And.from_pb(and_pb)

        assert expected_and == actual_and

    def test_not_equal_when_compared_with_different_type(self):
        an_and = And([Constraint("foo", Eq(True)), Constraint("bar", Eq(False))])
        not_an_and = tuple()

        assert an_and != not_an_and

    def test_raise_exception_when_and_has_less_than_2_subexpressions(self):
        """Test that we raise an exception when we try to instantiate an
        ``And`` object with a list of subexpressions of length less than 2."""

        with pytest.raises(ValueError, match="Invalid input value.*number of subexpression must be at least 2."):
            an_and = And([])


class TestOr:

    @given(or_constraints())
    def test_serialization(self, or_: Or):
        """Test that serialization and deserialization of ``Or`` objects work correctly."""

        expected_or = or_
        or_pb = or_.to_pb()  # type: query_pb2.Query.ConstraintExpr.Or
        actual_or = Or.from_pb(or_pb)

        assert expected_or == actual_or

    def test_not_equal_when_compared_with_different_type(self):
        an_or = Or([Constraint("foo", Eq(True)), Constraint("bar", Eq(False))])
        not_an_or = tuple()

        assert an_or != not_an_or

    def test_raise_exception_when_and_has_less_than_2_subexpressions(self):
        """Test that we raise an exception when we try to instantiate an
        ``Or`` object with a list of subexpressions of length less than 2."""

        with pytest.raises(ValueError, match="Invalid input value.*number of subexpression must be at least 2."):
            an_or = Or([])


class TestNot:

    @given(not_constraints())
    def test_serialization(self, not_: Not):
        """Test that serialization and deserialization of ``Not`` objects work correctly."""

        expected_not = not_
        not_pb = not_.to_pb()  # type: query_pb2.Query.ConstraintExpr.Not
        actual_not = Not.from_pb(not_pb)

        assert expected_not == actual_not

    def test_not_equal_when_compared_with_different_type(self):
        a_not = Not(Constraint("foo", Eq(True)))
        not_a_not = tuple()

        assert a_not != not_a_not


class TestQuery:

    @given(queries())
    def test_from_pb(self, query: Query):
        """Test that Query objects are correctly unpacked from the associated protobuf type."""

        expected_query = query
        query_pb = expected_query.to_pb()
        actual_query = Query.from_pb(query_pb)

        assert expected_query == actual_query

    def test_not_equal_when_compared_with_different_type(self):
        a_query = Query([Constraint("foo", Eq(0))], DataModel("bar", [AttributeSchema("foo", int, True)]))
        not_a_query = tuple()

        assert a_query != not_a_query

    def test_query_invalid_when_list_of_constraint_is_empty(self):
        """Test that we raise an exception when the list of query constraint is empty."""
        with pytest.raises(ValueError, match="Invalid input value for type.*empty list of constraints. "
                                             "The number of constraints must be at least 1."):
            a_query = Query([])

    def test_query_invalid_when_constraint_attribute_name_not_in_data_model(self):
        """Test that we raise an exception when at least one constraint attribute name
        is not present in the data model."""

        with pytest.raises(ValueError, match=""):
            a_query = Query([Constraint("an_attribute_name", Eq(0))], DataModel("a_data_model", []))

    def test_query_invalid_when_constraint_attribute_name_different_type(self):
        """Test that we raise an exception when at least one constraint attribute name
        has a different type wrt the data model."""

        with pytest.raises(ValueError, match=""):
            a_query = Query([Constraint("an_attribute_name", Eq(0))],
                            DataModel("a_data_model", [AttributeSchema("an_attribute_name", str, True)]))

