import errno
import os
from path import path
from setuptools import setup, find_packages


def read(rel_path):
    with open(os.path.join(path(__file__).parent, rel_path)) as f:
        ret = f.read()
    return ret

def readlines(rel_path):
    with open(os.path.join(path(__file__).parent, rel_path)) as f:
        ret = f.readlines()
    return ret


def mkdir_p(path):
    "recreate mkdir -p functionality"
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

mkdir_p('/usr/local/share/hendrix')

setup(
    author = "hangarunderground",
    author_email = "hendrix@reelio.com",
    name = "hendrix",
    packages = find_packages(),
    version = "0.1.1",
    url = "https://github.com/hangarunderground/hendrix",
    download_url = "https://github.com/hangarunderground/hendrix/tarball/v0.1.1-beta",
    description = "A deployment module for Django that uses Twisted.",
    long_description = read('docs/long_desc.html'),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords = ["django", "twisted", "async", "logging"],
    scripts = ['hendrix/utils/scripts/hx',],
    data_files = [
        ('/usr/local/bin', ['hendrix/utils/scripts/install-hendrix-service',]),
        ('/usr/local/share/hendrix', ['hendrix/utils/templates/init.d.j2',]),
    ],
    install_requires = readlines('requirements')
)
