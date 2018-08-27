import os

import jinja2
import yaml

from . import SHARE_PATH


def generateInitd(conf_file):
    """
    Helper function to generate the text content needed to create an init.d
    executable
    """
    allowed_opts = [
        'virtualenv', 'project_path', 'settings', 'processes',
        'http_port', 'cache', 'cache_port', 'https_port', 'key', 'cert'
    ]
    base_opts = ['--daemonize', ]  # always daemonize
    options = base_opts
    with open(conf_file, 'r') as cfg:
        conf = yaml.load(cfg)
    conf_specs = set(conf.keys())

    if len(conf_specs - set(allowed_opts)):
        raise RuntimeError('Improperly configured.')

    try:
        virtualenv = conf.pop('virtualenv')
        project_path = conf.pop('project_path')
    except:
        raise RuntimeError('Improperly configured.')

    cache = False
    if 'cache' in conf:
        cache = conf.pop('cache')
    if not cache:
        options.append('--nocache')

    workers = 0
    if 'processes' in conf:
        processes = conf.pop('processes')
        workers = int(processes) - 1
    if workers > 0:
        options += ['--workers', str(workers)]

    for key, value in conf.iteritems():
        options += ['--%s' % key, str(value)]

    with open(os.path.join(SHARE_PATH, 'init.d.j2'), 'r') as f:
        TEMPLATE_FILE = f.read()
    template = jinja2.Template(TEMPLATE_FILE)

    initd_content = template.render(
        {
            'venv_path': virtualenv,
            'project_path': project_path,
            'hendrix_opts': ' '.join(options)
        }
    )

    return initd_content
