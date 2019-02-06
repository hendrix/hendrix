import errno
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install

from hendrix import __version__


def file_name(rel_path):
    dir_path = os.path.dirname(__file__)
    return os.path.join(dir_path, rel_path)


def read(rel_path):
    with open(file_name(rel_path)) as f:
        return f.read()


def mkdir_p(path):
    "recreate mkdir -p functionality"
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


share_path = os.path.join(
    os.path.dirname(sys.executable),
    'share/hendrix'
)

mkdir_p(share_path)


INSTALL_REQUIRES = [
    'twisted',
    'cryptography>=2.3',
    'watchdog',
    'jinja2',
    'pychalk',
    'service-identity',
    'six',
    'autobahn'
]

EXTRAS = {
    'tests': [
        'pytest',
        'pytest-cov',
        'pytest-mock',
        'pytest-twisted',
        'django',
        'flask',
        'urllib3',
        'requests',
        'coverage'
        'codecov',
        'gunicorn'
    ]
}


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')
        if tag.startswith('v'):
            tag = tag[1:]

        version = __version__
        if version.startswith('v'):
            version = version[1:]

        if tag != version:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                os.getenv('CIRCLE_TAG'), __version__
            )
            sys.exit(info)


setup(
    name="hendrix",
    version=__version__,
    description="Pure python web server, based on Twisted, providing the One Obvious Way to do async and offbeat network traffic with django and other WSGI apps.",

    author="hendrix",
    author_email="justin@justinholmes.com",

    packages=find_packages(),

    url="https://github.com/hendrix/hendrix",
    download_url=(
            "https://github.com/hendrix/hendrix/tarball/"
            "v" + __version__
    ),

    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    ],
    keywords=["django", "twisted", "async", "logging", "wsgi"],
    scripts=[
        'hendrix/utils/scripts/hx',
        'hendrix/utils/scripts/hxw',
        'hendrix/utils/scripts/install-hendrix-service'
    ],
    data_files=[
        (share_path, ['hendrix/utils/templates/init.d.j2', ]),
    ],
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS,
    cmdclass={'verify': VerifyVersionCommand}

)
