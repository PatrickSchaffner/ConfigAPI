from tomli import loads
from tomli_w import dumps

from .types import TOMLDict, ConfigDict


class KeyCollisionException(Exception):
    
    def __init__(self, key:str, /) -> None:
        self._key = key
        super().__init__(f"Key '{key}' already assigned.")
    
    @property
    def key(self) -> str:
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
            if node not in current: current[node] = {}
            current = current[node]
            if not isinstance(current, dict):
                raise KeyCollisionException('.'.join(nodes[:i+1]))
        if leaf in current:
            raise KeyCollisionException(key)
        current[leaf] = value
    return nested


def parse_configs(toml_str : str) -> ConfigDict:
    return flat_dict(parse_toml(toml_str))


def format_configs(config_dict : ConfigDict) -> str:
    return format_toml(nested_dict(config_dict))
