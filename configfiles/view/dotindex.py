from typing import Tuple, List, Union

from .. import ConfigDict, ConfigValue


SEPARATOR = '.'


class DotIndexException(Exception):

    @classmethod
    def _join(cls, key:Union[str, List[str], Tuple[List[str], str]], /) -> str:
        if isinstance(key, str):
            return key
        if isinstance(key, tuple):
            key, leaf = key
            if leaf is not None:
                key = key + [leaf]
        if isinstance(key, list):
            return SEPARATOR.join(key)
        raise ValueError(f'Unexpected input type: {type(key)}')
    
    def __init__(self, key:Union[str, List[str], Tuple[List[str], str]], message:str, /):
        self._key = self._join(key)
        super().__init__(f"Error for entry '{self.key}': {message}")
    
    @property
    def key(self) -> str:
        return self._key


class NotFoundException(DotIndexException, KeyError):
    
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


def contains(configs:ConfigDict, key:str, /) -> bool:
    nodes, leaf = _split_key(key, leaf=True)
    parent = _deep_get(configs, nodes, raise_missing=False)
    return parent is not None and leaf in parent


def get(configs:ConfigDict, key:str, /, *,
        raise_missing: bool = True,
        ) -> ConfigValue:
    nodes, leaf = _split_key(key, leaf=True)
    return _deep_get(configs, nodes, leaf, raise_missing=raise_missing)


def set(configs:ConfigDict, key:str, value:ConfigValue, /, *,
        create_parents : bool = True,
        raise_missing : bool = False,
        typesafe_replace : bool = False,
        ) -> bool:
    nodes, leaf = _split_key(key, leaf=True)
    parent = _deep_get(configs, nodes, create_parents=create_parents, raise_missing=True)
    if leaf not in parent:
        if raise_missing:
            raise NotFoundException(key)
    else:
        prev = parent[leaf]
        if value == prev:
            return False
        if typesafe_replace and \
                value is not None and \
                prev is not None and \
                type(value) != type(prev):
            raise UnsafeReplaceException(key, type(value), type(prev))
    parent[leaf] = value
    return True


def delete(configs:ConfigDict, key:str, /, *,
           remove_empty : bool = True,
           raise_missing : bool = True,
           ) -> bool:
    nodes = _split_key(key)
    def _delete(dct:ConfigDict, current:str, children:List[str]) -> Tuple[bool,bool]:
        if current not in dct:
            if raise_missing: raise NotFoundException(key, node=current)
            else: return False, len(dct)==0
        if len(children) == 0:            
            del dct[current]
            return True, len(dct)==0
        nxt = dct[current]
        if not isinstance(nxt, dict):
            if raise_missing: raise NotFoundException(key, not_dict=current)
            else: return False, len(dct)==0
        changed, empty = _delete(nxt, children[0], children[1:])
        if changed and empty and remove_empty: del dct[current]
        return changed, len(dct)==0
    changed, _ = _delete(configs, nodes[0], nodes[1:])
    return changed


def _split_key(key:str, /, *, leaf=False):
    keys = key.split(SEPARATOR)
    if leaf:
        return keys[:-1], keys[-1]
    else:
        return keys


def _deep_get(configs:ConfigDict, nodes:List[str], /,
              leaf:str=None,
              *,
              create_parents=False,
              raise_missing=False,
              ) -> ConfigValue:
    current = configs
    for node in nodes:
        if node in current:
            current = current[node]
            if not isinstance(current, dict):
                if raise_missing:
                    raise NotFoundException((nodes, leaf), not_dict=node)
                else:
                    return None
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
        else:
            return None
    return current[leaf]
