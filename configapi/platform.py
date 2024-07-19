from pathlib import Path

from types import ModuleType
from typing import Tuple, Union

from platformdirs import user_config_path

from .api import Configs


class PlatformConfigs(Configs):

    def __init__(self, /,
                 defaults: Tuple[Union[str,ModuleType],str],
                 appname: str,
                 appauthor: str,
                 user_config_file: str,
                 project_config_file: Union[Path, str],
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_scope('defaults', defaults)
        self.add_scope('user', user_config_path(appname, appauthor, roaming=True, ensure_exists=True) / f'global-{user_config_file}', autosave_updates=False)
        self.add_scope('local', user_config_path(appname, appauthor, roaming=False, ensure_exists=True) / f'local-{user_config_file}')
        if project_config_file is not None:
            self.add_scope('project', project_config_file, autosave_updates=False)
