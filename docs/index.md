Twisted + Django = hendrix, a Python web server focused on making async and offbeat network traffic easy, fun, and fast.

*Mr. D. Reinhardt, with a pair of guitars and tatters of sheet music in the back seat, speeds his convertible westward over the mountains. The campfire carries on without the blessing of his gypsy jazz, but his morning return is as a fearsome, left-handed character – familiar but Twisted*`(.py)`

![hendrix](_static/hendrix-logo.png)

Dive in:    
```
$ sudo apt-get install build-essential libssl-dev libffi-dev python-dev
# (Maybe virtualenv stuff)
$ pip install hendrix
$ pip install django
$ django-admin startproject hey_joe
$ cd hey_joe
$ hx start

Starting Hendrix...
Ready and Listening on port 8000...
```

**hendrix** is a tool for handling bytes-on-the-wire to and from your python web application.  In this sense, it is similar to [mod_wsgi](https://modwsgi.readthedocs.org), [uWSGI](https://uwsgi-docs.readthedocs.org), and [gunicorn](http://gunicorn-docs.readthedocs.org).  

However, hendrix differs from these other technologies in that it is natively asynchronous and designed with background tasks in mind.  In this sense, it may serve some projects as a replacement for [gevent](https://readthedocs.org/projects/gevent/) or [celery](http://celery.readthedocs.org).  You'll be [amazed how easy it is](crosstown_traffic.md) to get started with async.

**hendrix** implements the WSGI protocol, so it can serve applications made with django, pyramid, flask and other WSGI frameworks.  However, hendrix views your web as just another network resource - in fact, this is central to the [hendrix philosophy](http://hendrix.readthedocs.org/en/latest/philosophy/).

More about the hendrix philosophy [here](philosophy.md).

## Getting started

See the [Quickstart](running-hendrix.md) or [FAQ](faq.md).
