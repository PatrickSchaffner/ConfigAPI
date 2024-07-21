from abc import abstractmethod, ABC
from types import ModuleType
from pathlib import Path
from pkgutil import get_data
from typing import Union

from .types import ConfigDict
from .toml import parse_configs, format_configs


class NotWritableException(Exception):
    pass


class ConfigSource(ABC):
    __slots__ = ()

    def read_dict(self) -> ConfigDict:
        return parse_configs(self.read_toml())
    
    def write_dict(self, configs_dict:ConfigDict):
        if self.read_only:
            raise NotWritableException(f"{type(self).__name__} is not writeable.")
        self.write_toml(format_configs(configs_dict))
    
    @property
    @abstractmethod
    def read_only(self) -> bool:
        raise NotImplementedError()
    
    @abstractmethod
    def read_toml(self) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def write_toml(self, configs_toml: str):
        raise NotImplementedError()


class FileConfigSource(ConfigSource):
    __slots__ = ('_file', '_read_only')
    
    def __init__(self, file: Union[str, Path], read_only:bool=False):
        self._file = Path(file)
        self._read_only = read_only
    
    @property
    def read_only(self) -> bool:
        return self._read_only
    
    @property
    def file(self) -> Path:
        return self._file
    
    def read_toml(self) -> str:
        return self._file.read_text() if self._file.exists() else ''
    
    def write_toml(self, configs_toml: str) -> None:
        self._file.write_text(configs_toml)


class PackageResourceConfigSource(ConfigSource):
    __slots__ = ('_resource', '_encoding')
    
    def __init__(self, module: Union[str, ModuleType], resource: str, encoding='utf8'):
        if isinstance(module, ModuleType):
            module = module.__name__
        self._resource = (module, resource)
        self._encoding = encoding
    
    @property
    def read_only(self) -> bool:
        return True
    
    def read_toml(self) -> str:
        return get_data(*self._resource).decode(self._encoding)
    
    def write_toml(self, _: str) -> None:
        raise NotWritableException('Cannot write to package resources.')
