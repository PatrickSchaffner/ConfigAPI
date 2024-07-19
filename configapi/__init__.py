__version__ = '0.0.1'

from .types import ConfigValue, ConfigDict
from .sources import FileConfigSource, PackageResourceConfigSource
from .api import Configs
from .platform import PlatformConfigs
