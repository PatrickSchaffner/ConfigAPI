from typing import Callable, Tuple, Dict, List, Set


from .types import KeyType, ConfigValue
from .patcher import Patcher, PatchType
from .scope import Scope, SourceType


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
