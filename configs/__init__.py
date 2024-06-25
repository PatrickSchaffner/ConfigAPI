from typing import Union, List, Dict

__version__ = '0.0.1'

ConfigValue = Union[bool, str, float, int, 'ConfigArray', 'ConfigDict']
ConfigArray = List[ConfigValue]
ConfigDict = Dict[str, ConfigValue]

from .manager import ConfigManager, DefaultConfigManager
from .sources import ConfigSource, FileConfigSource, PackageResourceConfigSource
