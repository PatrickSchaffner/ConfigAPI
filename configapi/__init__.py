__version__ = '0.0.1'

from .types import ConfigValue, ConfigDict
from .sources import FileConfigSource, PackageResourceConfigSource
from .manager import Configs

try:
    from .platform import PlatformConfigs
except ImportError:
    pass
