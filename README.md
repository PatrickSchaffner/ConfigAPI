# Config API

## Installation

> pip install configapi

## Basic Usage

Create a dictionary-like object that merges multiple TOML files.
``` {.python}
>>> from configapi import Config
>>> import somepackage.config

>>> configs = Config(sources={
...     'default': (somepackage.config, 'defaults.toml'),  # Read from package resource.
...     'user': Path.home() / 'user-config.toml',  # Read from textfile.
... })
>>> configs.load()
```
There are 3 kind of sources supported:
- Files: Specified as a path to a TOML file (pathlib.Path or str).
- Package file: Specified as a tuple with a package and a path to a file in the package.
- In-memory: Specified as a dictionary.

The configs object provides a dictionary-like interface to the
merged configuration, and to each source separately.
If multiple sources provide the same key, the value from the source
added last to the config container is used.
``` {.python}
>>> configs['project.authors']
['me']
>>> configs.default['project.authors']
['Bob', 'Alice']
>>> configs.source('project.authors')
'user'
```

Iterate over all entries. Optionally, the source can be included.
``` {.python}
>>> for (key, value, source) in configs.items(source=True):
...     print(f'{key}: {value} (from {source})')
project.authors: ['me'] (from user)
project.name: Example Project (from default)

```

Modifications must be done on the separate source dictionaries
(also called scopes). The changes are not saved automatically.
``` {.python}
>>> configs.user['project.name'] = 'My Project'
>>> configs.user.save()
>>> del configs.default['project.name']
>>> value, source, scope = configs.get('project.name', source=True, scope=True)
>>> print(f'{value} (from {source})')
My Project (from user)
>>> assert scope is configs.user
```

## Advanced Usage

The config files may be versioned, and upgrade patches applied automatically.
Specify the current version, or let it be inferred from the patches.
``` {.python}
>>> configs = Config(target_version='1.5.0')
```

Sources may be specified more explicitly for finer control.
The autosave feature ensures that changes applied by patches.
during loading are immediately saved back to the source.
``` {.python}
>>> local = FileConfigSource(Path.cwd() / 'local-config.toml', read_only=False)
>>> configs.add_source('local', local, autosave_updates=True)

>>> @configs.patch('0.2.1')
>>> def patch_0_2_1(cfg):
...    if 'project.author' in cfg:
...        cfg['project.authors'] = [cfg['project.author']]
...        del cfg['project.author']
...    return cfg

>>> configs.local.load()
```
If needed, individual sources may be (re-)loaded separately.
