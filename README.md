#Hendrix
###Twisted meets Django: *Making deployment easy*

Hendrix is a **multi-threaded**, **multi-process** *and* **asynchronous**
web server for *Django* projects. The idea here is to have a highly extensible
wsgi deployment tool that is fast, transparent and easy to use.

###Features
* **Multi-processing** - The WSGI app can be served from multiple
processes on a single machine. Meaning that it can leverage multicore
servers.
* **Optional Resource Caching** - Process distributed resource caching, dynamically serving
gzipped files. It's also possible to extend the current caching functionality by
subclassing the hendrix `CacheService` and adding a reference to that subclass within a
`HENDRIX_SERVICES` tuple of tuples e.g. `(('name', 'app.MyCustomCache'),)` in your
Django settings file. Just use the `--nocache` flag to turn caching off.
* **Built-in SSL Support** - SSL is also process distributed, just provide the options
--key /path/to/private.key and --cert /path/to/signed.cert to enable SSL
and process distributed TLS
* **Multi-threading from within Django** - Enables the use of Twisted's `defer`
module and `deferToThread` and `callInThread` methods from within Django
* **Built-in Websockets Framework**
* **Daemonize** by passing the `-d` or `--daemonize` flags to `hx`

###Installation

`pip install -e git+git@github.com:hangarunderground/hendrix.git@master#egg=hendrix`

###Deployment/Usage

Hendrix leverages the use of custom django management commands. That
and a little bash magic makes `hx` available as a shortcut to all of
the functionality you'd expect from `python manage.py hx`.

Include **hendrix** in your project's INSTALLED_APPS list
```python
INSTALLED_APPS = (
    ...,
    'hendrix',
    ...
)
```

Change your working directory to where manage.py lives:

`cd /path/to/project/`


#####For help and a complete list of the options:

`hx -h` or `hx --help`

#####Starting a server with 4 processes (1 parent and 3 child processes):

`hx start -w 3`

#####Stoping that server:

`hx stop`

*Note that stoping a server is dependent on the settings file and http_port
used.*

E.g. Running a server on port 8000 with local_settings.py would yield
8000_local_settings.pid which would be used to kill the server. I.e. if you
start with `hx start --settings local_settings` then stop by `hx stop --settings local_settings`

#####Restarting a server:

`hx restart`

###Serving Static Files
Serving static files via **Hendrix** is optional but easy.


a default static file handler is built into Hendrix which can be used by adding the following to your settings:
```
HENDRIX_CHILD_RESOURCES = (
    'hendrix.contrib.resources.static.DefaultDjangoStaticResource',
)
```
No other configuration is necessary.  You don't need to add anything to urls.py.

You can also easily create your own custom static or other handlers by adding them to HENDRIX\_CHILD\_RESOURCES.


###Running the Development Server
```
hx start --reload
```
This will reload your server every time a change is made to a python file in
your project.

###Twisted
Twisted is what makes this all possible. Mostly. Check it out [here](https://twistedmatrix.com/trac/).




###Yet to come
* Ensure stability of current implementation of web sockets
* Load Balancing
* tests...


###History
It started as a fork of the
[slashRoot deployment module](https://github.com/SlashRoot/WHAT/tree/44f50ee08c5d7acb74ed8a4ce928e85eb2dc714f/deployment).

The name is the result of some inane psychological formula wherein the
'twisted' version of Django Reinhardt is Jimi Hendrix.

Hendrix is currently maintained by [Reelio](reelio.com).
