from typing import Tuple, Dict, Callable, Union
from packaging.version import Version


from . import ConfigDict


PatchType = Callable[[ConfigDict], ConfigDict]
PatcherType = Callable[[ConfigDict], Tuple[ConfigDict, bool]]


class Patcher(object):

    def __init__(self, target_version: Union[str, Version] = None):
        self._target_version : Version = None if target_version is None else Version(target_version)
        self._patches : Dict[Version, PatchType] = {}
    
    @property
    def target_version(self) -> Version:
        return max(self._patches.keys()) if self._target_version is None else self._target_version

    def register(self, version: Union[str, Version], patch: PatchType) -> None:
        version = Version(version)
        if version in self._patches:
            raise ValueError(f"Multiple patches for version {version} registered.")
        self._patches[version] = patch
    
    def update(self, configs: ConfigDict) -> Tuple[ConfigDict, bool]:
        if len(self._patches) == 0:
            return configs, False
        target_version = self.target_version
        initial = Version(configs['version'] if 'version' in configs else '0.0.0')
        if initial >= target_version:
            return configs, False
        current = initial
        for (patch_version, patch_func) in self:
            if target_version < patch_version:
                break
            if current >= patch_version:
                continue
            configs = patch_func(configs)
            configs['version'] = str(patch_version)
            current = patch_version
        return configs, current > initial
    
    def __call__(self, configs: ConfigDict):
        return self.update(configs)

    def __iter__(self):
        return iter(sorted(self._patches.items()))
