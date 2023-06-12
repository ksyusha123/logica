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

from typing import Tuple, cast

from type_inference.type_inference_exception import TypeInferenceException
from type_inference.types.variable_types import AnyType, NumberType, StringType, ListType, RecordType, Type


def Rank(x):
  if isinstance(x, AnyType):
    return 0
  if isinstance(x, NumberType):
    return 1
  if isinstance(x, StringType):
    return 2
  if isinstance(x, ListType):
    return 3
  if isinstance(x, RecordType):
    if x.is_opened:
      return 4
    else:
      return 5


def Intersect(a: Type, b: Type, bounds: Tuple[int, int]) -> Type:
  if Rank(a) > Rank(b):
    a, b = b, a

  if isinstance(a, AnyType):
    return b

  if isinstance(a, NumberType) or isinstance(a, StringType):
    if a == b:
      return b
    raise TypeInferenceException(f'cannot match {str(a)} and {str(b)}', bounds)

  if isinstance(a, ListType):
    if isinstance(b, ListType):
      new_element = Intersect(a.element, b.element, bounds)
      return ListType(new_element)
    raise TypeInferenceException(f'cannot match {str(b)} and list', bounds)

  a = cast(RecordType, a)
  b = cast(RecordType, b)
  a_keys = set(a.fields.keys())
  b_keys = set(b.fields.keys())

  if a.is_opened:
    if b.is_opened:
      return IntersectFriendlyRecords(a, b, True, bounds)
    else:
      if a_keys <= b_keys:
        return IntersectFriendlyRecords(a, b, False, bounds)
      raise TypeInferenceException(f'cannot match types of record keys: {a_keys - b_keys}', bounds)
  else:
    if a_keys == b_keys:
      return IntersectFriendlyRecords(a, b, False, bounds)
    raise TypeInferenceException(f'cannot match types of records keys: {a_keys - (a_keys & b_keys)} and {b_keys - (a_keys & b_keys)}', bounds)


def IntersectFriendlyRecords(a: RecordType, b: RecordType, is_opened: bool, bounds: Tuple[int, int]) -> RecordType:
  result = RecordType({}, is_opened)
  for name, f_type in b.fields.items():
    if name in a.fields:
      intersection = Intersect(f_type, a.fields[name], bounds)
      result.fields[name] = intersection
    else:
      result.fields[name] = f_type
  return result


def IntersectListElement(a_list: ListType, b_element: Type, bounds: Tuple[int, int]) -> Type:
  return Intersect(a_list.element, b_element, bounds)
