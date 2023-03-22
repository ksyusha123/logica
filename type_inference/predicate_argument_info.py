
class PredicateArgumentInfo:
  def __init__(self, name: str, type: type):
    self.name = name
    self.type = type

  def __str__(self):
    return self.name