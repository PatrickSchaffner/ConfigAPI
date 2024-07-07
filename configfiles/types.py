from typing import Union, List, Dict


KeyType = str
ValueType = Union[bool, str, float, int]

TOMLValue = Union[ValueType, 'TOMLArray', 'TOMLDict']
TOMLArray = List[TOMLValue]
TOMLDict = Dict[KeyType, TOMLValue]

ConfigValue = Union[ValueType, 'ConfigArray']
ConfigArray = TOMLArray  # Array-contents are not flattened.
ConfigDict = Dict[KeyType, ConfigValue]
