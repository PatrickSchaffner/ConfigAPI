from pathlib import Path

from unittest.mock import patch

from configfiles.platform import PlatformConfigs
from configfiles.manager import Configs
from configfiles.types import ConfigDict


@patch('configfiles.platform.user_config_path')
def test_PlatformConfig(user_config_path, fs):

    def _usr_path(appname, appauthor, roaming=None, ensure_exists=None):
        usr_folder = Path('/userdata/') / ('roaming' if roaming else 'local') / appauthor / appname
        if ensure_exists and not usr_folder.exists():
            fs.create_dir(usr_folder)
        return usr_folder
    user_config_path.side_effect = _usr_path

    fs.create_file('/userdata/roaming/ACME/testapp/global-testapp-configs.toml', contents='version="0.5.0"\nproject.author = "me"')
    fs.create_file('./testapp.toml', contents='version="0.7.0"\nproject.name="Platform Test Project"')

    configs : Configs = PlatformConfigs(
        defaults=('tests.files', 'example-defaults.toml'),
        appname='testapp', appauthor='ACME',
        user_config_file='testapp-configs.toml',
        project_config_file=Path.cwd() / 'testapp.toml',
        target_version='1.0.0',
    )

    @configs.patch('0.6.0')
    def _patch(cfg: ConfigDict) -> ConfigDict:
        if 'project.author' in cfg:
            cfg['project.authors'] = [cfg['project.author']]
            del cfg['project.author']
        return cfg
    
    configs.load()
    
    assert configs.defaults['project.authors'] == ['dev', 'tester']
    assert configs.user['project.authors'] == ['me']
    assert 'project.author' not in configs.user
    assert 'project.authors' not in configs.local
    assert 'project.authors' not in configs.project
    assert configs['project.authors'] == ['me']
    assert configs['project.name'] == 'Platform Test Project'
    assert configs.local.keys() == {'version'}

    configs.local['project.authors'] = ['admin']
    assert configs['project.authors'] == ['admin']

    configs.local.save()
    cfgs = Path('/userdata/local/ACME/testapp/local-testapp-configs.toml').read_text()
    assert 'version = "0.6.0"' in cfgs
    assert '[project]\nauthors=[\n"admin",\n]' in cfgs.replace(' ', '')
