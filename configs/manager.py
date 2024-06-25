from pathlib import Path
from typing import Union, Dict, Tuple, List

from platformdirs import user_config_path
from mergedeep import merge, Strategy

from . import ConfigDict
from .container import ConfigContainer
from .sources import PackageResourceConfigSource, FileConfigSource
from .patcher import Patcher, PatchType


OriginValue = Union[List[str], 'OriginDict']
OriginDict = Dict[str, OriginValue]


class ConfigManager(object):
    
    def __init__(self, /, containers: List[ConfigContainer], *, version: str = None) -> None:
        self._containers: List[ConfigContainer] = [cnt for cnt in containers if cnt is not None]
        self._container_by_name: Dict[str, ConfigContainer] = {cnt.name: cnt for cnt in containers if cnt is not None}
        self._configs: ConfigDict = None
        self._origin: OriginDict = None
        self._patcher: Patcher = Patcher(target_version=version)
    
    def container(self, name: str) -> ConfigContainer:
        return self._container_by_name[name]
    
    @property
    def configs(self) -> ConfigDict:
        if self._configs is None:
            self._merge()
        return self._configs
    
    @property
    def origin(self) -> OriginDict:
        if self._origin is None:
            self._merge()
        return self._origin
    
    def patch(self, version: str):
        def patch_decorator(func: PatchType) -> PatchType:  
            self._patcher[version] = func
            return func
        return patch_decorator
    
    def update(self, configs: ConfigDict) -> Tuple[ConfigDict, bool]:
        return self._patcher(configs)
    
    def _merge(self) -> None:
        
        def _deep_merge(dicts: List[ConfigDict], **kwargs) -> ConfigDict:
            return merge({}, *dicts, **kwargs)
        
        self._configs = _deep_merge([
            container.configs for container in reversed(self._containers)
        ], strategy=Strategy.TYPESAFE_REPLACE)
        del self._configs['version']
        
        def _copy_origin(configs: ConfigDict, origin: str) -> OriginValue:
            return {key: _copy_origin(value, origin) if isinstance(value, dict) else [origin]
                    for (key, value) in configs.items() if value is not None}
        
        self._origin = _deep_merge([
            _copy_origin(container.configs, container.name) for container in reversed(self._containers)
        ], strategy=Strategy.TYPESAFE_ADDITIVE)
        del self._origin['version']
        
        def _invert_arrays(node: OriginDict):
            for (key, child) in list(node.items()):
                if isinstance(child, dict):
                    _invert_arrays(child)
                elif isinstance(child, list):
                    node[key] = list(reversed(child))
                else:
                    raise RuntimeError("Unexpected type '{type(chile)}' in OriginDict.")
        
        _invert_arrays(self._origin)


class DefaultConfigManager(ConfigManager):
    
    def __init__(self, /,
        author_name : str = None,
        app_name : str = None,
        user_config_file : str = None,
        defaults_config_file : str = None,
        project_config_file : Union[str, Path] = None,
        **kwargs
    ) -> None:
        if defaults_config_file is None:
            self._defaults = None
        else:
            defaults_module, defaults_file = defaults_config_file.split('/', 1)
            self._defaults = ConfigContainer('defaults', PackageResourceConfigSource(defaults_module, defaults_file))
        
        if user_config_file is None:
            self._local = None
            self._global = None
        else:
            if user_config_file.endswith('.toml'):
                user_config_file = user_config_file[:-5]
                
            def _user_config(name:str, synced:bool=False) -> ConfigContainer:
                user_dir = user_config_path(
                    appname=app_name,
                    appauthor=author_name,
                    ensure_exists=True,
                    roaming=synced,
                )
                source = FileConfigSource(user_dir / f'{name}-{user_config_file}.toml')
                container = ConfigContainer(name, source, autosave_updates=not synced, patcher=self.update)
                return container
            
            self._local = _user_config('local', synced=False)
            self._user = _user_config('global', synced=True)
        
        if project_config_file is None:
            self._project = None
        else:
            self._project = ConfigContainer(
                'project',
                FileConfigSource(project_config_file),
                autosave_updates=False,
                patcher=self.update,
            )
        
        super().__init__([self._project, self._local, self._user, self._defaults], **kwargs)
    
    @property
    def defaults(self):
        return self._defaults
    
    @property
    def user(self):
        return self._user
    
    @property
    def local(self):
        return self._local
    
    @property
    def project(self):
        return self._project
