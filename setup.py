from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = read('README.md')

setup(
    name = "hendrix",
    packages = find_packages(),
    version = "0.1",
    url = "https://github.com/hangarunderground/hendrix",
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
    scripts = ['hendrix/hendrix-deploy.py'],
)
