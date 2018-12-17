.. _query-language:

The Query Language
==================

We recommend reading:ref:`defining-data-model` before reading this section.

Along with the Data Model language, the SDK offers the possibility to specify `queries` defined over data models.

The :mod:`~oef.query` module implements the API that allows you to:

* Query the OEF Node about specific kind of services
* Query other agents to ask them the desired resources.

In one sentence, a `query` is a set of `constraints`, defined over a `data model`.
The outcome is a set of `description` (that is, instances of :class:`~oef.schema.Description`)
`matching` with the query. That is, all the description whose attributes satisfy the constraints in the query.

In the next sections, we describe how to build queries with the SDK.

Constraints
-----------

A `constraint` is associated with an `attribute` and imposes restrictions on the domain of that attribute.
That is, it imposes some limitations on the values the attribute can assume.

We have different types of constraints:

* `relation` constraints:

  * the author of the book must be `Stephen King`
  * the publication year must be greater than 1990

* `set` constraints:

  * the genre must fall into the following set of genres: `Horror`, `Science fiction`, `Non-fiction`.

* `range` constraints:

  * the average rating must be between 3.5 and 4.5

* any conjunction/disjunction of the previous constraints:

  * books that belong to `Horror` **and** has been published after 2000
  * books whose author is **either** `J. K. Rowling` **or** `J. R. R. Tolkien`

The class that implements the constraint concept is :class:`~oef.query.Constraint`
In the following, we show how to define them in the Python SDK.

Relation
~~~~~~~~

The :class:`~oef.query.Relation` is a constraint type that allows you to impose specific values for the attributes.

The types of relation constraints are:

* Equal: :class:`~oef.query.Eq`
* Not Equal: :class:`~oef.query.NotEq`
* Less than: :class:`~oef.query.Lt`
* Less than or Equal: :class:`~oef.query.LtEq`
* Greater than: :class:`~oef.query.Gt`
* Greater than or Equal: :class:`~oef.query.GtEq`

**Examples**: using the attributes we used before: :ref:`defining-data-model`

.. code-block:: python

    from oef.query import Constraint, Eq, NotEq, Lt, LtEq, Gt, GtEq

    # all the books whose author is Stephen King
    Constraint(attr_author,  Eq("Stephen King"))

    # all the books that are not of the genre Horror
    Constraint(attr_genre,   NotEq("Horror"))

    # all the books published before 1990
    Constraint(attr_year,    Lt(1990))

    # the same of before, but including 1990
    Constraint(attr_year,    LtEq(1990))

    # all the books with rating greater than 4.0
    Constraint(attr_avg_rat, Gt(4.0))

    # all the books published after 2000, included
    Constraint(attr_year,    GtEq(2000))



Set
~~~

The :class:`~oef.query.Set` is a constraint type that allows you to restrict the values of the attribute
in a specific set.

There are two kind of ``Set`` constraints:

* In (a set of values): :class:`~oef.query.In`
* Not in (a set of values): :class:`~oef.query.NotIn`


**Examples**:

.. code-block:: python

    from oef.query import Constraint, In, NotIn

    # all the books whose genre is one of `Horror`, `Science fiction`, `Non-fiction`
    Constraint(attr_genre,   In(["horror", "science fiction", "non-fiction"])

    # all the books that have not been published neither in 1990, nor in 1995, nor in 2000
    Constraint(attr_year,   NotIn([1990, 1995, 2000]))


Range
~~~~~

The :class:`~oef.query.Range` is a constraint type that allows you to restrict the values of the attribute in a given
range.


**Examples**:

.. code-block:: python

    from oef.query import Constraint, Range

    # all the books whose title is between 'A' and 'B' (alphanumeric order)
    Constraint(attr_title,   Range("A", "B"))

    # all the books that have been published between 1960 and 1970
    Constraint(attr_genre,   Range(1960, 1970))

And
~~~

The :class:`~oef.query.And` is a constraint type that allows you to specify a conjunction of constraints
over an attribute. That is, the ``And`` constraint is satisfied whenever all the constraints that constitute
the `and` are satisfied.


**Example**:

.. code-block:: python

    from oef.query import Constraint, And, NotEq, Range

    # all the books whose title is between 'I' and 'J' (alphanumeric order) but not equal to 'It'
    Constraint(attr_title,   And([Range("I", "J"), NotEq("It")])

Or
~~

The :class:`~oef.query.Or` is a constraint type that allows you to specify a disjunction of constraints. That is, the
``Or`` constraint is satisfied whenever at least one of the constraints that constitute the ``or`` is satisfied.


**Example**:

.. code-block:: python

    from oef.query import Constraint, Or, Lt, Gt

    # all the books that have been published either before the year 1960 or after the year 1970
    Constraint(attr_year,   Or([Lt(1960), Gt(1970)]))


Queries
-------

A `query` is simply a `list of constraints`, interpreted as a conjunction (that is, a matching description with
the query must satisfy `every` constraint.)

**Examples**:

.. code-block:: python

    from oef.query import Query, Constraint, Eq, Gt, Eq

    # return all the books written by Stephen King published after 1990, and available as an e-book:
    Query([
        Constraint(attr_author, Eq("Stephen King")),
        Constraint(attr_year, Gt(1990)),
        Constraint(attr_ebook, Eq(True))
    ], book_model)

Where ``book_model`` is the ``DataModel`` object defined in :ref:`defining-data-model`. However, the data model is
an optional parameter, but to avoid ambiguity is recommended to include it.
