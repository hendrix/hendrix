*Mr. D. Reinhardt, with a pair of guitars and tatters of sheet music in the back seat, speeds his convertible westward over the mountains. The campfire carries on without the blessing of his gypsy jazz, but his morning return is as a fearsome, left-handed character – familiar but Twisted*`(.py)`

![hendrix](docs/_static/hendrix-logo.png)

*v3.2.3*

*A Python web server that makes async and offbeat network traffic easy, fun, and fast.*

[![Gitter](https://badges.gitter.im/hendrix/hendrix.svg)](https://gitter.im/hendrix/hendrix?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Build Status](https://travis-ci.org/hendrix/hendrix.png?branch=master)](https://travis-ci.org/hendrix/hendrix)[![Latest Docs](https://readthedocs.org/projects/hendrix/badge/?version=latest)](http://hendrix.readthedocs.org/en/latest/)

## Overview

**hendrix** is a tool for handling bytes-on-the-wire to and from your python web application.  In this sense, it is similar to [mod_wsgi](https://modwsgi.readthedocs.org), [uWSGI](https://uwsgi-docs.readthedocs.org), and [gunicorn](http://gunicorn-docs.readthedocs.org).  

However, hendrix differs from these other technologies in that it is natively asynchronous and designed with background tasks in mind.  In this sense, it may serve some projects as a replacement for [gevent](https://readthedocs.org/projects/gevent/) or [celery](http://celery.readthedocs.org).

**hendrix** implements the WSGI protocol, so it can serve applications made with django, pyramid, flask and other WSGI frameworks.  However, hendrix views your web as just another network resource - in fact, this is central to the [hendrix philosophy](http://hendrix.readthedocs.org/en/latest/philosophy/).

Twisted is one of the most battle-tested and actively developed Python projects.  Until hendrix, however, Twisted has not been part of a mainstream python web server.  And that's a shame.

### Features
* **Multi-processing** - The WSGI app can be served from multiple
processes on a single machine.
* **Multi-threading from within your Django / Flask / Pyramid app**: Various APIs allow you to defer logic until later, place it in a different thread or process, and report back asynchronously.  For example, see [crosstown_traffic](http://hendrix.readthedocs.org/en/latest/crosstown_traffic/).
* **Built-in Websockets Framework**
* **Optional Resource Caching**
* **Built-in SSL Support**: Terminate SSL inside your app if you like.  Public keys can be part of your logic!
* **Daemonize** by passing the `-d` or `--daemonize` flags to `hx`

### Quickstart

Using pip

    pip install hendrix


#### Running the Development Server

cd to the directory where your **manage.py** file is located and...

    hx start --dev

This is roughly the equivalent of running the django devserver.

----

**For more, see the full [hendrix documentation](http://hendrix.readthedocs.org).**
