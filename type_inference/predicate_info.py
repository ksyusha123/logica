from re import sub

from type_inference.predicate_argument_info import PredicateArgumentInfo


class PredicateInfo:
  def __init__(self, name: str, *args: PredicateArgumentInfo):
    self.name = self.__format_name(name)
    self.args = args

  def _format_name(self, string):
    result = sub(r"([_\-])+", " ", string).title().replace(" ", "")
    return ''.join([result[0].upper(), result[1:]])

  def __str__(self):
    return f'{self.name}({", ".join([str(arg) for arg in self.args])})'

