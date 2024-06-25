from typing import Tuple, List, Union

from . import ConfigDict, ConfigValue


SEPARATOR = '.'


class DotIndexException(Exception):

    @classmethod
    def _join(cls, key:Union[str, List[str], Tuple[List[str], str]], /) -> str:
        if isinstance(key, str):
            return key
        if isinstance(key, tuple):
            key, leaf = key
            key = key + [leaf]
        if isinstance(nodes, list):
            return SEPARATOR.join(nodes if leaf is None else nodes + [leaf])
        raise ValueError(f'Unexpected input type: {type(key)}')
    
    def __init__(self, key:Union[str, List[str], Tuple[List[str], str]], message:str, /):
        self._key = _join(key)
        super().__init__(f"Error for entry '{self.key}': {message}")
    
    @property
    def key(self) -> str:
        return self._key


class NotFoundException(DotIndexException):
    
    def __init__(self, key:Union[str, List[str], Tuple[List[str], str]], /, *,
                 node : str = None,
                 not_dict : str = None
                 ) -> None:
        if not_dict is None:
            if node is None:
                msg = f"Entry does not exist."
            else:
                msg = f"Node '{node}' does not exist."
        else:
            msg = f"Node '{not_dict}' is not a dict."
        super().__init__(key, msg)


class UnsafeReplaceException(DotIndexException):
    
    def __init__(self, key:Union[str, List[str], Tuple[List[str], str]], /,
                 type_new:type, type_replaced:type) -> None:
        msg = f"Type unsafe replacement from {type_replaced} to {type_new}."
        super().__init__(key, msg)


def dotindex_contains(toml_dict:ConfigDict, key:str, /) -> bool:
    nodes, leaf = _split_key(key, leaf=True)
    parent = _deep_get(toml_dict, nodes, raise_missing=False)
    return parent is not None and leaf in parent


def dotindex_get(toml_dict:ConfigDict, key:str, /, *,
                 raise_missing: bool = True,
                 ) -> ConfigValue:
    nodes, leaf = _split_key(key, leaf=True)
    return _deep_get(toml_dict, nodes, leaf, raise_missing=raise_missing)


def dotindex_set(toml_dict:ConfigDict, key:str, value:ConfigValue, /, *,
                 create_parents : bool = True,
                 raise_missing : bool = False,
                 typesafe_replace : bool = False,
                 ) -> None:
    nodes, leaf = _split_key(key, leaf=True)
    parent = _deep_get(toml_dict, nodes, create_parents=create_parents, raise_missing=True)
    if leaf not in parent:
        if raise_missing:
            raise NotFoundException(key)
    elif typesafe_replace and \
            value is not None and \
            parent[leaf] is not None and \
            type(value) != type(parent[leaf]):
        raise UnsafeReplaceException(key, type(value), type(parent[leaf]))
    parent[leaf] = value


def dotindex_delete(toml_dict:ConfigDict, key:str, /, *,
                    remove_empty : bool = True,
                    raise_missing : bool = True,
                    ) -> None:

    def _delete(dct:ConfigDict, current:str, children:List[str]) -> bool:
        if current not in dct:
            if raise_missing:
                raise NotFoundException(key, node=current)
        elif len(children) == 0:            
            del dct[current]
        else:
            nxt = dct[current]
            if not isinstance(nxt, dict):
                if raise_missing:
                    raise NotFoundException(key, not_dict=current)
                return False
            elif _delete(nxt, children[0], children[1:]) and remove_empty:
                del dct[current]
        return len(dct) == 0
    
    nodes = _split_key(key)
    _delete(toml_dict, nodes[0], nodes[1:])


class DotIndex(object):

    def __init__(self, target:ConfigDict) -> None:
        self._target = target
    
    def __getitem__(self, key:str) -> ConfigValue:
        return dotindex_get(self._target, key)
    
    def __setitem__(self, key:str, val:ConfigValue) -> None:
        dotindex_set(self._target, key, val)
    
    def __delitem__(self, key:str) -> None:
        dotindex_delete(self._target, key)
    
    def __contains__(self, key:str) -> bool:
        return dotindex_contains(self._target, key)


def _split_key(key:str, /, *, leaf=False):
    keys = key.split(SEPARATOR)
    if leaf:
        return keys[:-1], keys[-1]
    else:
        return keys


def _deep_get(toml_dict:ConfigDict, nodes:List[str], /,
              leaf:str=None,
              *,
              create_parents=False,
              raise_missing=False,
              ) -> ConfigValue:
    current = toml_dict
    for node in nodes:
        if node in current:
            current = current[node]
            if not isinstance(current, dict):
                raise NotFoundException((nodes, leaf), not_dict=node)
        elif create_parents:
            current[node] = dict()
            current = current[node]
        elif raise_missing:
            raise NotFoundException((nodes, leaf), not_dict=node)
        else:
            return None
    if leaf is None:
        return current
    if leaf not in current:
        if raise_missing:
            raise NotFoundException((nodes, leaf))
        return None
    return current[leaf]
