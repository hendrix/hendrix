import errno
import os
from setuptools import setup, find_packages


def file_name(rel_path):
    dir_path = os.path.dirname(__file__)
    return os.path.join(dir_path, rel_path)

def read(rel_path):
    with open(file_name(rel_path)) as f:
        ret = f.read()
    return ret

def readlines(rel_path):
    with open(file_name(rel_path)) as f:
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
    scripts = [
        'hendrix/utils/scripts/hx',
        'hendrix/utils/scripts/install-hendrix-service'
    ],
    data_files = [
        ('/usr/local/share/hendrix', ['hendrix/utils/templates/init.d.j2',]),
    ],
    install_requires = readlines('requirements')
)
