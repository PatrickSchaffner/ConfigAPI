from typing import Union, Tuple, KeysView, ItemsView, ValuesView
from types import ModuleType
from pathlib import Path

from .types import ConfigDict, KeyType, ConfigValue
from .sources import (
    ConfigSource,
    InMemoryConfigSource,
    FileConfigSource,
    PackageResourceConfigSource,
    NotWritableException)
from .patcher import Patcher, PatcherType


SourceType = Union[ConfigSource, str, Path, Tuple[ModuleType, str], Tuple[str, str], ConfigDict]


class Scope(object):
    __slots__ = ('_source', '_patcher', '_autosave_updates', '_configs', '_version')

    def __init__(self, /, source: SourceType, patcher: Patcher = None, *,
                 autosave_updates: bool = None,
                 ) -> None:
        if isinstance(source, (str, Path)):
            source = FileConfigSource(source)
        elif isinstance(source, tuple):
            source = PackageResourceConfigSource(*source)
        elif isinstance(source, dict):
            source = InMemoryConfigSource(source)
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
