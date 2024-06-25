from typing import Tuple, Callable

from . import ConfigDict
from .sources import ConfigSource
from .patcher import PatcherType


class ConfigContainer(object):
    
    def __init__(self, /,
                 name: str,
                 source: ConfigSource,
                 *,
                 autosave_updates: bool = None,
                 patcher: PatcherType = None,
                 ) -> None:
        self._name : str = name
        self._source : ConfigSource = source
        self._autosave_updates: bool = autosave_updates if autosave_updates is not None else not source.read_only
        self._configs: ConfigDict = None
        self._patcher: PatcherType = patcher if patcher is not None else lambda configs: (configs, False)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def source(self) -> ConfigSource:
        return self._source
     
    @property
    def autosave_updates(self) -> bool:
        return self._autosave_updates
    
    @property
    def configs(self) -> str:
        if self._configs is None:
            self.load()
        return self._configs
    
    def load(self) -> None:
        self._configs, updated = self._patcher(self.source.read_dict())
        if updated and self.autosave_updates:
            self.save()
    
    def save(self) -> None:
        if self.source.read_only:
            raise RuntimeError(f"Config source '{self.name}' is not writeable.")
        self.source.write_dict(self._configs)
