from hendrix import __version__
import errno
import os
import sys
from setuptools import setup, find_packages


def file_name(rel_path):
    dir_path = os.path.dirname(__file__)
    return os.path.join(dir_path, rel_path)


def read(rel_path):
    with open(file_name(rel_path)) as f:
        return f.read()


def readlines(rel_path):
    with open(file_name(rel_path)) as f:
        ret = f.readlines()
    return ret


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

setup(
    name="hendrix",
    version=__version__,
    description="Pure python web server, based on Twisted, providing the One Obvious Way to do async and offbeat network traffic with django and other WSGI apps.",

    author="hangarunderground",
    author_email="justin@justinholmes.com",

    packages=find_packages(),

    url="https://github.com/hangarunderground/hendrix",
    download_url=(
        "https://github.com/hangarunderground/hendrix/tarball/"
        "v" + __version__
    ),

    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 4 - Beta',
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
        'hendrix/utils/scripts/install-hendrix-service'
    ],
    data_files=[
        (share_path, ['hendrix/utils/templates/init.d.j2', ]),
    ],
    install_requires=readlines('requirements.txt'),
    extras_require={
        'ssl': ['pyopenssl', ],
        'dev': readlines('requirements_dev.txt'),
    }
)
