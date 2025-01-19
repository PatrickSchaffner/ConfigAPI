from abc import abstractmethod, ABC
from types import ModuleType
from pathlib import Path
from pkgutil import get_data
from typing import Union, Tuple
from copy import deepcopy

from .types import ConfigDict
from .toml import parse_configs, format_configs


class NotWritableException(Exception):
    pass


class ConfigSource(ABC):
    __slots__ = ('_read_only',)

    def __init__(self, read_only: bool = False):
        self._read_only = read_only

    def read_dict(self) -> ConfigDict:
        return parse_configs(self.read_toml())
    
    def write_dict(self, configs_dict: ConfigDict):
        if self.read_only:
            raise NotWritableException(f"{type(self).__name__} is not writeable.")
        self.write_toml(format_configs(configs_dict))
    
    @property
    def read_only(self) -> bool:
        return self._read_only
    
    @abstractmethod
    def read_toml(self) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def write_toml(self, configs_toml: str):
        raise NotImplementedError()


class InMemoryConfigSource(ConfigSource):
    __slots__ = ('_configs',)

    def __init__(self, configs: ConfigDict = None, **kwargs):
        self._configs = configs if configs is not None else dict()
        super(InMemoryConfigSource, self).__init__(**kwargs)

    @property
    def configs(self):
        return self._configs

    @configs.setter
    def configs(self, value: ConfigDict):
        self._configs = value

    def read_toml(self) -> str:
        return format_configs(self._configs)

    def write_toml(self, configs_toml: str):
        self.write_dict(parse_configs(configs_toml))

    def write_dict(self, configs_dict: ConfigDict):
        if self.read_only:
            raise NotWritableException(f"{type(self).__name__} is not writeable.")
        self._configs.clear()
        self._configs.update(deepcopy(configs_dict))

    def read_dict(self) -> ConfigDict:
        return deepcopy(self._configs)


class FileConfigSource(ConfigSource):
    __slots__ = ('_file',)
    
    def __init__(self, file: Union[str, Path], **kwargs):
        self._file = Path(file)
        super(FileConfigSource, self).__init__(**kwargs)
    
    @property
    def file(self) -> Path:
        return self._file
    
    def read_toml(self) -> str:
        return self._file.read_text() if self._file.exists() else ''
    
    def write_toml(self, configs_toml: str) -> None:
        self._file.write_text(configs_toml)


class PackageResourceConfigSource(ConfigSource):
    __slots__ = ('_resource', '_encoding')
    
    def __init__(self, module: Union[str, ModuleType], resource: str, encoding: str = 'utf8'):
        if isinstance(module, ModuleType):
            module = module.__name__
        self._resource: Tuple[str, str] = (module, resource)
        self._encoding: str = encoding
        super(PackageResourceConfigSource, self).__init__(read_only=True)
    
    @property
    def resource(self) -> Tuple[str,str]:
        return self._resource
    
    @property
    def encoding(self) -> str:
        return self._encoding
    
    def read_toml(self) -> str:
        return get_data(*self.resource).decode(self.encoding)
    
    def write_toml(self, _: str) -> None:
        raise NotWritableException('Cannot write to package resources.')
