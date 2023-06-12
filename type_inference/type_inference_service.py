#!/usr/bin/python
#
# Copyright 2023 Logica
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import cast

from type_inference.inspectors.inspector_base import Inspector
from type_inference.intersection import Intersect, IntersectListElement
from type_inference.types.edge import Equality, EqualityOfElement, FieldBelonging
from type_inference.types.expression import PredicateAddressing
from type_inference.types.types_graph import TypesGraph
from type_inference.types.variable_types import AnyType, ListType, RecordType


class TypeInference:
  def __init__(self, graphs: dict, inspector: Inspector = None):
    self.inspector = inspector
    self.all_edges = []
    for graph in graphs.values():
      self.all_edges.extend(graph.ToEdgesSet())
    self.MergeGraphs(graphs)

  @staticmethod
  def GetEdgeContainingSameExpression(predicate_addressing: PredicateAddressing, graph: TypesGraph):
    for key, value in graph.expression_connections.items():
      if str(key) == str(predicate_addressing):
        return list(value.values())[0][0]

  @staticmethod
  def FindField(predicate_addressing: PredicateAddressing, graph: TypesGraph):
    edge = TypeInference.GetEdgeContainingSameExpression(predicate_addressing, graph)
    if edge.vertices[0] == predicate_addressing:
      return edge.vertices[0]
    else:
      return edge.vertices[1]

  def MergeGraphs(self, graphs: dict):
    edges_to_add = []
    for predicate_name, graph in graphs.items():
      for p in graph.expression_connections:
        if isinstance(p, PredicateAddressing) and p.type == AnyType() and p.predicate_name != predicate_name:
          if p.predicate_name in graphs:
            to_link = self.FindField(p, graphs[p.predicate_name])
            edges_to_add.append(Equality(p, to_link, (-1, -1)))
          else:
            column_info = self.inspector.TryGetColumnsInfo(p.predicate_name)
            p.type = column_info[p.field]
    self.all_edges.extend(edges_to_add)

  def Infer(self):
    changed = True
    while changed:
      changed = False
      for edge in self.all_edges:
        if isinstance(edge, Equality):
          edge = cast(Equality, edge)
          left, right = edge.left.type, edge.right.type
          result = Intersect(left, right, edge.bounds)
          if result != edge.left.type:
            edge.left.type = result
            changed = True
          if result != edge.right.type:
            edge.right.type = result
            changed = True
        elif isinstance(edge, EqualityOfElement):
          edge = cast(EqualityOfElement, edge)
          if isinstance(edge.list.type, AnyType):
            edge.list.type = ListType(AnyType())
          left, right = edge.element.type, cast(ListType, edge.list.type)
          result = IntersectListElement(right, left, edge.bounds)
          if result != edge.element.type:
            edge.element.type = result
            changed = True
          if ListType(result) != edge.list.type:
            edge.list.type = ListType(result)
            changed = True
        elif isinstance(edge, FieldBelonging):
          edge = cast(FieldBelonging, edge)
          if isinstance(edge.parent.type, AnyType):
            edge.parent.type = RecordType({}, True)
          record = cast(RecordType, edge.parent.type)
          field_name = edge.field.subscript_field
          if field_name in record.fields:
            result = Intersect(edge.field.type, record.fields[field_name], edge.bounds)
            if result != record.fields[field_name]:
              changed = True
              record.fields[field_name] = result
          else:
            changed = True
            record.fields[field_name] = edge.field.type
