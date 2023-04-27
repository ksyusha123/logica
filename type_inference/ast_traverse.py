from json import dumps
from collections import defaultdict

from parser_py import parse
from type_inference.types.edge import Equality, EqualityOfElement
from type_inference.types.expression import StringLiteral, NumberLiteral, BooleanLiteral, NullLiteral, ListLiteral, \
  PredicateAddressing, Variable
from type_inference.types.types_graph import TypesGraph


def get_literal_expression(types_graph: TypesGraph, literal: dict):
  if "the_string" in literal:
    return StringLiteral()
  elif "the_number" in literal:
    return NumberLiteral()
  elif "the_bool" in literal:
    return BooleanLiteral()
  elif "the_null" in literal:
    return NullLiteral()
  elif "the_list" in literal:
    return ListLiteral([convert_expression(types_graph, expression) for expression in literal["the_list"]["element"]])
  else:
    return None


def fill_fields(predicate_name: str, types_graph: TypesGraph, value: dict):
  for i in value["record"]["field_value"]:
    value = convert_expression(types_graph, i["value"]["expression"])
    predicate_field = PredicateAddressing(predicate_name, i["field"])
    e = Equality(predicate_field, value, bounds=(0, 0))
    types_graph.connect(e)


def convert_expression(types_graph: TypesGraph, expression: dict):
  if "literal" in expression:
    return get_literal_expression(types_graph, expression["literal"])

  if "variable" in expression:
    return Variable(expression["variable"]["var_name"])

  if "call" in expression:
    call = expression["call"]
    predicate_name = call["predicate_name"]
    fill_fields(predicate_name, types_graph, call)
    return PredicateAddressing(predicate_name, "logica_value")

  if "subscript" in expression:
    pass


def process_predicate(types_graph: TypesGraph, value: dict):
  predicate_name = value["predicate_name"]
  fill_fields(predicate_name, types_graph, value)


def fill_field(types_graph: TypesGraph, field: dict):
  variable = Variable(field["field"])

  if "expression" not in field["value"]:
    raise NotImplementedError(field)

  value = convert_expression(types_graph, field["value"]["expression"])
  e = Equality(variable, value, bounds=(0, 0))
  types_graph.connect(e)


def fill_conjunct(types_graph: TypesGraph, conjunct: dict):
  if "unification" in conjunct:
    unification = conjunct["unification"]
    left_hand_side = convert_expression(types_graph, unification["left_hand_side"])
    right_hand_side = convert_expression(types_graph, unification["right_hand_side"])
    e = Equality(left_hand_side, right_hand_side, bounds=(0, 0))
    types_graph.connect(e)
  elif "inclusion" in conjunct:
    inclusion = conjunct["inclusion"]
    l = convert_expression(types_graph, inclusion["list"])
    element = convert_expression(types_graph, inclusion["element"])
    e = EqualityOfElement(l, element, bounds=(0, 0))
    types_graph.connect(e)
  elif "predicate" in conjunct:
    process_predicate(types_graph, conjunct["predicate"])
  else:
    raise NotImplementedError(conjunct)


def traverse_tree(rule: dict):
  types_graph = TypesGraph()

  for field in rule["head"]["record"]["field_value"]:
    fill_field(types_graph, field)

  if "body" in rule:
    for conjunct in rule["body"]["conjunction"]["conjunct"]:
      fill_conjunct(types_graph, conjunct)

  return types_graph


def run(raw_program: str):
  parsed = parse.ParseFile(raw_program)
  graphs = defaultdict(lambda: TypesGraph())

  for rule in parsed["rule"]:
    predicate_name = rule["head"]["predicate_name"]
    graphs[predicate_name] |= traverse_tree(rule)

  return graphs


if __name__ == '__main__':
  s1 = "Test(x:, y:) :- x in l, l == [0, 0.5, 1.0, 1.5, 2.0], y == 3 - x;"
  s3 = """
StructureExtractionTest(x:, w:) :-
  StructureTest(a:),
  x == a.x,
  w == a.z.w;"""
  s4 = "ByRoleCount(role:, count? += 1) distinct :- Employee(role:);"

  s = [
    s1,
    s3,
    s4,
    "Q(x) :- T(x), Num(x);",
    "Q(x + y) :- T(x), T(y);",
    "Q(x) :- T(x), T(y), Str(x), x == y;",
    "Q(x ++ y) :- T(x), T(y);",
    "Q(y) :- T(x), y in x, Num(y);",
    "Q(Str(y)) :- T(x), y == x.a;",
    "Q(a:, b:) :- T(x), T(y), a == x * y, b == x + y;"
  ]

  for i in s:
    print(i)

    try:
      graphs = run(i)

      for predicate_name, graph in graphs.items():
        print(predicate_name)
        print(dumps(graph.to_serializable_edges_list()))
        print()
    except Exception as e:
      print("bad")
      print()
