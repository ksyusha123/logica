import sys

from parser_py import parse
from type_inference.types.types_graph import TypesGraph, UnificationContext


def get_involved_variable_name(expression: dict):
  while "subscript" in expression:
    expression = expression["subscript"]["record"]

  return expression["variable"]["var_name"]


def connect_unification(types_graph: TypesGraph, left_variable: str,
                        right_variable: str, unification):
  types_graph.connect(left_variable, right_variable, unification)


def fill_conjunct(types_graph: TypesGraph, conjunct: dict):
  if "unification" in conjunct:
    unification = conjunct["unification"]
    left_variable = get_involved_variable_name(unification["left_hand_side"])
    right_variable = get_involved_variable_name(unification["right_hand_side"])
    connect_unification(types_graph, left_variable, right_variable, unification)
  elif "inclusion" in conjunct:
    pass
  elif "predicate" in conjunct:
    pass
  else:
    pass


def fill_field(types_graph: TypesGraph, field: dict):
  value = field["value"]["expression"]
  var_name = field["field"]
  var_context = {"variable": {"var_name": var_name}}

  if "call" in value:
    call = value["call"]
    predicate_name = call["predicate_name"]
    pseudo_variable = predicate_name + call["record"]["field_value"]["field"]
    connect_unification(types_graph, var_name, pseudo_variable,
                        UnificationContext(var_context, value))
  elif "variable" in value:
    if var_name != field["field"]:
      second_variable = value["variable"]["var_name"]
      connect_unification(types_graph, var_name, second_variable,
                          UnificationContext(var_context, value))
  elif "subscript" in value:
    second_variable = value["variable"]["var_name"]
    connect_unification(types_graph, var_name, second_variable,
                        UnificationContext(var_context, value))
  else:
    raise NotImplementedError(value)


def traverse_tree(rule: dict):
  types_graph = TypesGraph()

  for field in rule["head"]["record"]["field_value"]:
    fill_field(types_graph, field)

  for conjunct in rule["body"]["conjunction"]["conjunct"]:
    fill_conjunct(types_graph, conjunct)

  return types_graph


def run(raw_program: str):
  parsed = parse.ParseFile(raw_program)
  graphs = dict()

  for rule in parsed["rule"]:
    graphs[rule["head"]["predicate_name"]] = traverse_tree(rule)

  # todo: use this result - separate task


if __name__ == '__main__':
  run(sys.argv[1])
