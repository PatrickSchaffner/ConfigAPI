from typing import Union, List, Dict

__version__ = '0.0.1'

from .types import ConfigValue, ConfigDict
from .sources import ConfigSource, FileConfigSource, PackageResourceConfigSource

from .view import ConfigView
