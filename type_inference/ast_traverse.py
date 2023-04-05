import sys

from json import dumps
from collections import defaultdict

from parser_py import parse
from type_inference.types.types_graph import TypesGraph


combines_counter = 0


def get_literal_var(literal):
  if "the_string" in literal:
    return literal["the_string"]["the_string"]
  elif "the_number" in literal:
    return literal["the_number"]["number"]
  elif "the_bool" in literal:
    return literal["the_bool"]["the_bool"]
  elif "the_null" in literal:
    return literal["the_null"]["the_null"]
  else:
    return None


def get_predicate_name_and_pseudo_var(call):
  predicate_name = call["predicate_name"]
  pseudo_variable = predicate_name + ":result"
  return predicate_name, pseudo_variable


def get_involved_variable_name(expression: dict):
  if "literal" in expression:
    return get_literal_var(expression["literal"])

  if "combine" in expression:
    global combines_counter
    combines_counter += 1
    return "Combine" + str(combines_counter)

  if "variable" not in expression and "subscript" not in expression:
    return get_predicate_name_and_pseudo_var(expression["call"])[1]

  while "subscript" in expression:
    expression = expression["subscript"]["record"]

  return expression["variable"]["var_name"]


def process_predicate(types_graph, value):
  call = value["predicate"]
  predicate_name = get_predicate_name_and_pseudo_var(call)[0]

  for i in call["record"]["field_value"]:
    arg_name = predicate_name + ":" + str(i["field"])
    _fill_field(types_graph, arg_name, call, i["value"]["expression"])


def process_list(types_graph: TypesGraph, var_name: str, var_context: dict,
                 elements: list):
  for e in elements:
    _fill_field(types_graph, var_name, var_context, e)


def process_literal(types_graph: TypesGraph, var_name: str, var_context: dict,
                    value: dict):
  literal = value["literal"]
  pseudo_variable = get_literal_var(literal)

  if pseudo_variable:
    types_graph.connect(var_name, pseudo_variable, var_context, value)
  else:
    process_list(types_graph, var_name, var_context,
                 literal["the_list"]["element"])


def process_call(types_graph, value, var_context, var_name):
  call = value["call"]
  predicate_name, pseudo_variable = get_predicate_name_and_pseudo_var(call)
  types_graph.connect(var_name, pseudo_variable, var_context, value)

  for i in call["record"]["field_value"]:
    arg_name = predicate_name + ":" + str(i["field"])
    _fill_field(types_graph, arg_name, call, i["value"]["expression"])


def process_record(types_graph, var_name, var_context, value):
  for field in value["record"]["field_value"]:
    name = field["field"]
    sub_context = {
      "record": var_context,
      "subscript":
        {
          "literal":
            {
              "the_symbol":
                {
                  "symbol": name
                }
            }
        }
    }

    _fill_field(types_graph, var_name, sub_context,
                field["value"]["expression"])


def _fill_field(types_graph: TypesGraph, var_name: str, var_context: dict,
                value: dict):
  if "literal" in value:
    process_literal(types_graph, var_name, var_context, value)
  elif "subscript" in value or "variable" in value:
    second_variable = get_involved_variable_name(value)
    types_graph.connect(var_name, second_variable, var_context, value)
  elif "implication" in value:
    implication = value["implication"]
    _fill_field(types_graph, var_name, var_context, implication["otherwise"])

    for i in implication["if_then"]:
      _fill_field(types_graph, var_name, var_context, i["consequence"])
      process_call(types_graph, i["condition"], var_context, var_name)
  elif "call" in value:
    process_call(types_graph, value, var_context, var_name)
  elif "record" in value:
    process_record(types_graph, var_name, var_context, value)
  elif "combine" in value:
    raise NotImplementedError("not yet ready")


def fill_field(types_graph: TypesGraph, field: dict):
  var_name = field["field"]
  var_context = {"variable": {"var_name": var_name}}
  value = field["value"]["expression"]
  _fill_field(types_graph, var_name, var_context, value)


def fill_conjunct(types_graph: TypesGraph, conjunct: dict):
  if "unification" in conjunct:
    unification = conjunct["unification"]
    left_hand_side = unification["left_hand_side"]
    right_hand_side = unification["right_hand_side"]
    left_variable = get_involved_variable_name(left_hand_side)
    right_variable = get_involved_variable_name(right_hand_side)

    types_graph.connect(left_variable, right_variable, left_hand_side,
                        right_hand_side)
  elif "inclusion" in conjunct:
    inclusion = conjunct["inclusion"]
    var_context = inclusion["element"]
    var_name = get_involved_variable_name(var_context)
    elements = inclusion["list"]["literal"]["the_list"]["element"]
    process_list(types_graph, var_name, var_context, elements)
  elif "predicate" in conjunct:
    process_predicate(types_graph, conjunct)


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
  print(parsed)

  for rule in parsed["rule"]:
    g = traverse_tree(rule)
    graphs[rule["head"]["predicate_name"]] |= g
    print(dumps(graphs[rule["head"]["predicate_name"]].variable_connections))

  # todo: use this result - separate task


if __name__ == '__main__':
  run(sys.argv[1])
