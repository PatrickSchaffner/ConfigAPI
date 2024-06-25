from abc import abstractmethod, ABC
from types import ModuleType
from pathlib import Path
from pkgutil import get_data
from typing import Dict, List, Union

from tomli import loads
from tomli_w import dumps

from . import ConfigDict


def parse_toml(toml : str) -> ConfigDict:
    return loads(toml)


def format_toml(toml_dict : ConfigDict) -> str:
    return dumps(toml_dict)



class ConfigSource(ABC):

    def read_dict(self) -> ConfigDict:
        return parse_toml(self.read_toml())
    
    def write_dict(self, configs_dict:ConfigDict):
        self.write_toml(format_toml(configs_dict))
    
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
    
    def __init__(self, file: Union[str, Path], read_only:bool=False):
        file = Path(file)
        self._file = file
        self._read_only = read_only
    
    @property
    def read_only(self) -> bool:
        return self._read_only
    
    def read_toml(self) -> str:
        return self._file.read_text() if self._file.exists() else ''
    
    def write_toml(self, configs_toml: str) -> None:
        if self.read_only:
            raise RuntimeError(f"FileConfigSource is not writeable.")
        self._file.write_text(configs_toml)


class PackageResourceConfigSource(ConfigSource):
    
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
    
    def write_toml(self, configs_toml: str) -> None:
        raise RuntimeError('Cannot write to package resources.')
