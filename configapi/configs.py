from typing import Callable, Dict, List, Set


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

    def scope(self, name: str) -> Scope:
        return self._scopes[name]

    def __getattr__(self, name: str) -> Scope:
        try:
            return self.scope(name)
        except KeyError:
            raise AttributeError(name)

    def patch(self, version: str, /) -> Callable[[PatchType], PatchType]:
        def _decorator(patch: PatchType) -> PatchType:
            self._patcher.register(version=version, patch=patch)
            return patch

        return _decorator

    def load(self) -> None:
        for scope in self._scopes.values():
            scope.load()

    def keys(self) -> Set[str]:
        for key, _ in self.items():
            yield key

    def items(self, source=False, scope=False):
        processed = set()
        for name in reversed(self._priority):
            s = self._scopes[name]
            for (key, value) in s.items():
                if key in processed:
                    continue
                result = [key, value]
                if source:
                    result.append(name)
                if scope:
                    result.append(s)
                yield tuple(result)
                processed.add(key)

    def values(self):
        for _, value in self.items():
            yield value

    def get(self, key: KeyType, source=False, scope=False) -> ConfigValue:
        for src in reversed(self._priority):
            scp = self._scopes[src]
            if key in scp:
                result = [scp[key]]
                if source:
                    result.append(src)
                if scope:
                    result.append(scp)
                return tuple(result) if len(result) > 1 else result[0]
        raise KeyError(key)

    def __getitem__(self, key: KeyType) -> ConfigValue:
        return self.get(key)

    def __contains__(self, key: KeyType) -> bool:
        return any(key in scope for scope in self._scopes.values())

    def source(self, key: KeyType) -> str:
        _, source = self.get(key, source=True)
        return source
