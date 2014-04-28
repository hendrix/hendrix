import errno
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def mkdir_p(path):
    "recreate mkdir -p functionality"
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

README = read('README.md')

mkdir_p('/usr/local/share/hendrix')

setup(
    name = "hendrix",
    packages = find_packages(),
    version = "v0.1.1-beta",
    url = "https://github.com/hangarunderground/hendrix",
    download_url = "https://github.com/hangarunderground/hendrix/tarball/v0.1.1-beta",
    description = "A deployment module for Django that uses Twisted.",
    long_description = "\n\n".join([README]),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords = ["django", "twisted", "async", "logging"],
    scripts = ['hendrix/utils/scripts/hx',],
    data_files = [
        ('/usr/local/bin', ['hendrix/utils/scripts/install-hendrix-service',]),
        ('/usr/local/share/hendrix', ['hendrix/utils/templates/init.d.j2',]),
    ],
    install_requires = open('requirements').readlines(),
)
