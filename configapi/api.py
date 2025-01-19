from typing import Union, Callable, Tuple, Dict, List, KeysView, ItemsView, ValuesView, Set
from types import ModuleType
from pathlib import Path

from .types import ConfigDict, KeyType, ConfigValue
from .sources import (
    ConfigSource,
    FileConfigSource,
    PackageResourceConfigSource,
    NotWritableException)
from .patcher import Patcher, PatchType, PatcherType


SourceType = Union[ConfigSource, str, Path, Tuple[ModuleType, str], Tuple[str, str]]


class Scope(object):
    __slots__ = ('_source', '_patcher', '_autosave_updates', '_configs', '_version')
    
    def __init__(self, /, source: SourceType, patcher: Patcher = None, *,
                 autosave_updates: bool = None,
                 ) -> None:
        if isinstance(source, (str, Path)):
            source = FileConfigSource(source)
        elif isinstance(source, tuple):
            source = PackageResourceConfigSource(*source)
        elif not isinstance(source, ConfigSource):
            raise ValueError(f"Argument 'source' of type '{type(source)}' is not a ConfigSource.")
        self._source: ConfigSource = source
        self._patcher: PatcherType = patcher if patcher is not None else lambda cfg: (cfg, False)
        self._autosave_updates: bool = autosave_updates if autosave_updates is not None else self.writable
        self._configs: ConfigDict = None
        self._version: str = None
    
    @property
    def writable(self) -> bool:
        return not self._source.read_only
    
    @property
    def autosave_updates(self) -> bool:
        return self._autosave_updates
    
    @property
    def source(self) -> ConfigSource:
        return self._source
    
    def load(self) -> None:
        (self._configs, changed) = self._patcher(self._source.read_dict())
        if 'version' in self._configs:
            self._version = self._configs['version']
            del self._configs['version']
        if changed and self.autosave_updates:
            self.save()
    
    def keys(self) -> KeysView:
        return self._configs.keys()
    
    def items(self) -> ItemsView:
        return self._configs.items()
    
    def values(self) -> ValuesView:
        return self._configs.values()
    
    def __contains__(self, key: KeyType) -> bool:
        return key in self._configs

    def __getitem__(self, key: KeyType) -> ConfigValue:
        return self._configs[key]
    
    def __setitem__(self, key: KeyType, value: ConfigValue) -> None:
        self._check_writable()
        self._configs[key] = value
    
    def __delitem__(self, key: KeyType) -> None:
        self._check_writable()
        del self._configs[key]

    def save(self) -> None:
        self._check_writable()
        if self._version is not None:
            self._configs['version'] = self._version
        self._source.write_dict(self._configs)
        if 'version' in self._configs:
            del self._configs['version']
    
    def _check_writable(self) -> None:
        if not self.writable:
            raise NotWritableException("Scope is not writable.")
    

class Configs(object):
    __slots__ = ('_patcher', '_scopes', '_priority')

    def __init__(self, /, sources: Dict[str, SourceType] = None, *, target_version: str = None) -> None:
        self._patcher: Patcher = Patcher(target_version=target_version)
        self._scopes: Dict[str, Scope] = {}
        self._priority: List[str] = []
        if isinstance(sources, dict):
            for (name, source) in sources.items():
                self.add_source(name, source)
    
    def add_source(self, /, name: str, source: SourceType, **kwargs) -> Scope:
        scope = Scope(source, self._patcher, **kwargs)
        self._scopes[name] = scope
        self._priority.append(name)
        return scope
    
    def __getattr__(self, name: str) -> Scope:
        if name not in self._scopes:
            raise AttributeError(name)
        else:
            return self._scopes[name]

    def patch(self, version: str, /) -> Callable[[PatchType], PatchType]:
        def _decorator(patch: PatchType) -> PatchType:
            self._patcher.register(version=version, patch=patch)
            return patch
        return _decorator
    
    def load(self) -> None:
        for scope in self._scopes.values():
            scope.load()
    
    def keys(self) -> Set[str]:
        all_keys: Set[str] = set()
        for scope in self._scopes.values():
            all_keys = all_keys.union(set(scope.keys()))
        return all_keys
    
    def items(self, source=False):
        processed = set()
        for name in reversed(self._priority):
            scope = self._scopes[name]
            for (key, value) in scope.items():
                if key in processed:
                    continue
                yield (key, value, name) if source else (key, value)
                processed.add(key)

    def values(self):
        return (self[key] for key in self.keys())

    def _lookup_scope(self, key: KeyType) -> Scope:
        for name in reversed(self._priority):
            scope = self._scopes[name]
            if key in scope:
                return scope
        raise KeyError(key)

    def _lookup(self, key: KeyType) -> Tuple[ConfigValue, str]:
        for source in reversed(self._priority):
            scope = self._scopes[source]
            if key in scope:
                return scope[key], source
        raise KeyError(key)
    
    def __getitem__(self, key: KeyType) -> ConfigValue:
        value, _ = self._lookup(key)
        return value
    
    def __contains__(self, key: KeyType) -> bool:
        return any(key in scope for scope in self._scopes.values())
    
    def source(self, key: KeyType) -> str:
        _, source = self._lookup(key)
        return source
