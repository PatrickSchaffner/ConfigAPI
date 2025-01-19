from pathlib import Path

from pytest import raises

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

    assert configs.default is configs.scope('default')
    assert configs.project is configs.scope('project')

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
    assert configs.get('project.authors', source=True, scope=True) == (['me'], 'project', configs.project)

    assert 'project.authors' in configs
    assert set(configs.keys()) == {'project.authors', 'project.name'}
    assert all(i in [('project.authors', ['me'], 'project', configs.project),
                     ('project.name', 'Example test project', 'default', configs.default),
                     ] for i in configs.items(source=True, scope=True))
    assert all(v in ['Example test project', ['me']] for v in configs.values())


def test_Configs_errors():
    configs = Configs(sources={'main': dict()})
    configs.load()

    with raises(KeyError) as exc_info:
        _ = configs['non.existent']
    assert type(exc_info.value) == KeyError

    with raises(AttributeError) as exc_info:
        _ = configs.not_main
    assert type(exc_info.value) == AttributeError
