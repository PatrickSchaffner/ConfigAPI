from tomli import loads
from tomli_w import dumps

from .types import TOMLDict, TOMLValue, ConfigDict, KeyType


class KeyCollisionException(Exception):
    
    def __init__(self, key:KeyType, /) -> None:
        self._key : KeyType = key
        super().__init__(f"Key '{key}' already assigned.")
    
    @property
    def key(self) -> KeyType:
        return self._key


def parse_toml(toml_str : str) -> TOMLDict:
    return loads(toml_str)


def format_toml(toml_dict : TOMLDict) -> str:
    return dumps(toml_dict)


def flat_dict(nested_dict : TOMLDict) -> ConfigDict:
    flat = {}
    def _flatten(nested : TOMLDict, base:str=''):
        if len(base) > 0: base += '.'
        for (key, value) in nested.items():
            if isinstance(value, dict):
                _flatten(value, base=base+key)
            else:
                flat[base+key] = value
    _flatten(nested_dict)
    return flat


def nested_dict(flat_dict : ConfigDict) -> TOMLDict:
    nested : TOMLDict = {}
    for (key, value) in flat_dict.items():
        keys = key.split('.')
        nodes, leaf = keys[:-1], keys[-1]
        current : TOMLDict = nested
        for i, node in enumerate(nodes):
            if node not in current:
                nxt : TOMLDict = {}
                current[node] = nxt
            else:
                nxt : TOMLValue = current[node]
                if not isinstance(nxt, dict):
                    raise KeyCollisionException('.'.join(nodes[:i+1]))
            current = nxt
        if leaf in current:
            raise KeyCollisionException(key)
        current[leaf] = value
    return nested


def parse_configs(toml_str : str) -> ConfigDict:
    return flat_dict(parse_toml(toml_str))


def format_configs(config_dict : ConfigDict) -> str:
    return format_toml(nested_dict(config_dict))
