from pathlib import Path


from configapi.types import ConfigDict
from configapi.configs import Configs

from . import files


def test_Configs(fs):
    cfg_proj = Path('project-configs.toml')
    fs.create_file(cfg_proj, contents='version="0.8.5"\nproject.author = "me"')

    configs: Configs = Configs({
        'default': (files, 'example-defaults.toml'),
        'project': cfg_proj,
    }, target_version='1.0.0')

    @configs.patch('0.9.2')
    def _patch(cfgs: ConfigDict) -> ConfigDict:
        if 'project.author' in cfgs:
            if 'project.authors' not in cfgs:
                cfgs['project.authors'] = [cfgs['project.author']]
            del cfgs['project.author']
        return cfgs

    configs.load()
    assert configs.project['project.authors'] == ['me']
    assert configs.default['project.authors'] == ['dev', 'tester']
    assert configs['project.authors'] == ['me']
    assert configs.source('project.authors') == 'project'
    assert configs.source('project.name') == 'default'
