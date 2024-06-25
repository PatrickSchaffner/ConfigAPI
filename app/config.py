from typing import Dict, Any
from pathlib import Path

from configs import DefaultConfigManager, ConfigManager, ConfigDict
from configs.dotindex import DotIndex

from . import __version__

configs: ConfigManager = DefaultConfigManager(
    author_name='ACME',
    app_name='app',
    user_config_file='app-config.toml',
    defaults_config_file='app/defaults-config.toml',
    project_config_file=Path.cwd() / 'app.toml',
    version=__version__,
)


@configs.patch('1.0.2')
def patch_102(configs: ConfigDict) -> ConfigDict:
    _move_config_entry(configs, 'user', 'name')
    return configs


@configs.patch('1.0.12')
def patch_1012(configs: ConfigDict) -> ConfigDict:
    _move_config_entry(configs, 'name', 'username')
    _move_config_entry(configs, 'project.url', 'project.repo.url')
    return configs


def _move_config_entry(configs: ConfigDict, old_name: str, new_name: str) -> None:
    cfg = DotIndex(configs)
    if old_name in cfg:
        if new_name not in cfg:
            cfg[new_name] = cfg[old_name]
        del cfg[old_name]
