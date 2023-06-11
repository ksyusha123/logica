from collections import defaultdict
from typing import Dict

from parser_py import parse
from type_inference.types.edge import Equality, EqualityOfElement, FieldBelonging, PredicateArgument
from type_inference.types.expression import StringLiteral, NumberLiteral, BooleanLiteral, NullLiteral, ListLiteral, \
  PredicateAddressing, SubscriptAddressing, Variable, RecordLiteral, Literal, Expression
from type_inference.types.types_graph import TypesGraph


class TypesGraphBuilder:
  _predicate_usages: defaultdict
  _if_statements_counter: int

  def __init__(self):
    self.bounds = (0, 0)  # todo calculate bounds
    self.ResetInternalState()

  def ResetInternalState(self):
    self._predicate_usages = defaultdict(lambda: 0)
    self._if_statements_counter = 0

  def Run(self, parsed_program: dict) -> Dict[str, TypesGraph]:
    self.ResetInternalState()
    graphs = defaultdict(lambda: TypesGraph())

    for rule in parsed_program['rule']:
      predicate_name = rule['head']['predicate_name']
      graphs[predicate_name] |= self.TraverseTree(predicate_name, rule)

    return graphs

  def TraverseTree(self, predicate_name: str, rule: dict) -> TypesGraph:
    types_graph = TypesGraph()

    for field in rule['head']['record']['field_value']:
      self.FillField(types_graph, predicate_name, field)

    if 'body' in rule:
      for conjunct in rule['body']['conjunction']['conjunct']:
        self.FillConjunct(types_graph, conjunct)

    return types_graph

  def FillField(self, types_graph: TypesGraph, predicate_name: str, field: dict):
    field_name = field['field']

    if isinstance(field_name, int):
      field_name = f'col{field_name}'

    variable = PredicateAddressing(predicate_name, field_name, self._predicate_usages[predicate_name])

    if 'aggregation' in field['value']:
      value = self.ConvertExpression(types_graph, field['value']['aggregation']['expression'])
      types_graph.Connect(Equality(variable, value, self.bounds))
      return

    if 'expression' in field['value']:
      value = self.ConvertExpression(types_graph, field['value']['expression'])
      types_graph.Connect(Equality(variable, value, self.bounds))
      return

    raise NotImplementedError(field)

  def FillConjunct(self, types_graph: TypesGraph, conjunct: dict):
    if 'unification' in conjunct:
      unification = conjunct['unification']
      left_hand_side = self.ConvertExpression(types_graph, unification['left_hand_side'])
      right_hand_side = self.ConvertExpression(types_graph, unification['right_hand_side'])
      types_graph.Connect(Equality(left_hand_side, right_hand_side, self.bounds))
    elif 'inclusion' in conjunct:
      inclusion = conjunct['inclusion']
      list_of_elements = self.ConvertExpression(types_graph, inclusion['list'])
      element = self.ConvertExpression(types_graph, inclusion['element'])
      types_graph.Connect(EqualityOfElement(list_of_elements, element, self.bounds))
    elif 'predicate' in conjunct:
      value = conjunct['predicate']
      self.FillFields(value['predicate_name'], types_graph, value)
    else:
      raise NotImplementedError(conjunct)

  def FillFields(self, predicate_name: str, types_graph: TypesGraph, fields: dict, result: PredicateAddressing = None):
    for field in fields['record']['field_value']:
      value = self.ConvertExpression(types_graph, field['value']['expression'])
      field_name = field['field']

      if isinstance(field_name, int):
        field_name = f'col{field_name}'

      predicate_field = PredicateAddressing(predicate_name, field_name, self._predicate_usages[predicate_name])
      types_graph.Connect(Equality(predicate_field, value, self.bounds))

      if result:
        types_graph.Connect(PredicateArgument(result, predicate_field, self.bounds))

  def ConvertExpression(self, types_graph: TypesGraph, expression: dict) -> Expression:
    if 'literal' in expression:
      return self.ConvertLiteralExpression(types_graph, expression['literal'])

    if 'variable' in expression:
      return Variable(expression['variable']['var_name'])

    if 'call' in expression:
      call = expression['call']
      predicate_name = call['predicate_name']
      result = PredicateAddressing(predicate_name, 'logica_value', self._predicate_usages[predicate_name])
      self.FillFields(predicate_name, types_graph, call, result)
      self._predicate_usages[predicate_name] += 1
      return result

    if 'subscript' in expression:
      subscript = expression['subscript']
      record = self.ConvertExpression(types_graph, subscript['record'])
      field = subscript['subscript']['literal']['the_symbol']['symbol']
      result = SubscriptAddressing(record, field)
      types_graph.Connect(FieldBelonging(record, result, self.bounds))
      return result

    if 'record' in expression:
      record = expression['record']
      field_value = record['field_value']
      return RecordLiteral(
        {field['field']: self.ConvertExpression(types_graph, field['value']['expression']) for field in field_value})

    if 'implication' in expression:
      implication = expression['implication']
      inner_variable = Variable(f'_IfNode{self._if_statements_counter}')
      self._if_statements_counter += 1
      otherwise = self.ConvertExpression(types_graph, implication['otherwise'])
      types_graph.Connect(Equality(inner_variable, otherwise, self.bounds))

      for i in implication['if_then']:
        self.ConvertExpression(types_graph, i['condition'])
        value = self.ConvertExpression(types_graph, i['consequence'])
        types_graph.Connect(Equality(inner_variable, value, self.bounds))

      return inner_variable

  def ConvertLiteralExpression(self, types_graph: TypesGraph, literal: dict) -> Literal:
    if 'the_string' in literal:
      return StringLiteral()
    elif 'the_number' in literal:
      return NumberLiteral()
    elif 'the_bool' in literal:
      return BooleanLiteral()
    elif 'the_null' in literal:
      return NullLiteral()
    elif 'the_list' in literal:
      return ListLiteral(
        [self.ConvertExpression(types_graph, expression) for expression in literal['the_list']['element']])
