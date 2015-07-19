#Installation

You'll need to use **virtualenv**. If you don't have that set up, follow [the virtualenv instructions here.](http://docs.python-guide.org/en/latest/dev/virtualenvs/)

Inside your python virtuaenv:

```bash
$ pip install hendrix
```

The following python packages are dependencies that should be automaticly installed.

```bash
twisted
txsockjs
zope.interface
watchdog
jinja2
pychalk==0.0.5
service_identity
```

###Extra Setup for SSL

```bash
$ sudo apt-get install build-essential libssl-dev libffi-dev python-dev
$ pip install cryptography
```

For usage details, see [Quickstart](quickstart.md).
