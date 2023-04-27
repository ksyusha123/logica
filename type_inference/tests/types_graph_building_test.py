import unittest

from type_inference import ast_traverse
from type_inference.types import edge, expression


def _reset_id(l):
  for i in l:
    for v in i.vertices:
      v._id = 0


class TestTypesGraphBuilding(unittest.TestCase):
  def _compare_without_id(self, actual, expected):
    _reset_id(actual)
    _reset_id(expected)

    self.assertCountEqual(actual, expected)

  def test_when_connection_with_other_predicates(self):
    s = "Q(x) :- T(x), Num(x)"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    expected = [edge.Equality(expression.Variable('col0'), expression.Variable('x'), (0, 0)),
                edge.Equality(expression.Variable('x'), expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(expression.Variable('x'), expression.PredicateAddressing('Num', 'col0'), (0, 0))]

    self._compare_without_id(edges, expected)

  def test_when_plus_operator(self):
    s = "Q(x + y) :- T(x), T(y);"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    x_var = expression.Variable('x')
    y_var = expression.Variable('y')
    expected = [edge.Equality(expression.Variable('col0'), expression.PredicateAddressing('+', 'logica_value'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('+', 'left'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('+', 'right'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('T', 'col0'), (0, 0))]

    self._compare_without_id(edges, expected)

  def test_when_str(self):
    s = "Q(x) :- T(x), T(y), Str(x), x == y;"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    x_var = expression.Variable('x')
    y_var = expression.Variable('y')
    expected = [edge.Equality(expression.Variable('col0'), expression.Variable('x'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('Str', 'col0'), (0, 0)),
                edge.Equality(x_var, y_var, (0, 0))]

    self._compare_without_id(edges, expected)

  def test_when_concat_operator(self):
    s = "Q(x ++ y) :- T(x), T(y);"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    x_var = expression.Variable('x')
    y_var = expression.Variable('y')
    expected = [
      edge.Equality(expression.Variable('col0'), expression.PredicateAddressing('++', 'logica_value'), (0, 0)),
      edge.Equality(x_var, expression.PredicateAddressing('++', 'left'), (0, 0)),
      edge.Equality(y_var, expression.PredicateAddressing('++', 'right'), (0, 0)),
      edge.Equality(x_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
      edge.Equality(y_var, expression.PredicateAddressing('T', 'col0'), (0, 0))]

    self._compare_without_id(edges, expected)

  def test_when_in_operator(self):
    s = "Q(y) :- T(x), y in x, Num(y);"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    x_var = expression.Variable('x')
    y_var = expression.Variable('y')
    expected = [edge.Equality(expression.Variable('col0'), y_var, (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('Num', 'col0'), (0, 0)),
                edge.EqualityOfElement(x_var, y_var, (0, 0))]

    self._compare_without_id(edges, expected)

  def test_when_record(self):
    s = "Q(p: Str(y), q: z + w, s: x) :- T(x), y == x.a, z == x.b, w == x.c.d;"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    pass

  def test_when_named_columns(self):
    s = "Q(a:, b:) :- T(x), T(y), a == x + y, b == x + y;"

    graph = ast_traverse.run(s)["Q"]
    edges = graph.to_edges_list()

    x_var = expression.Variable('x')
    y_var = expression.Variable('y')
    a_var = expression.Variable('a')
    b_var = expression.Variable('b')
    expected = [edge.Equality(a_var, a_var, (0, 0)),
                edge.Equality(b_var, b_var, (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('T', 'col0'), (0, 0)),
                edge.Equality(a_var, expression.PredicateAddressing('+', 'logica_value'), (0, 0)),
                edge.Equality(b_var, expression.PredicateAddressing('+', 'logica_value'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('+', 'left'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('+', 'right'), (0, 0)),
                edge.Equality(x_var, expression.PredicateAddressing('+', 'left'), (0, 0)),
                edge.Equality(y_var, expression.PredicateAddressing('+', 'right'), (0, 0))]

    self._compare_without_id(edges, expected)
