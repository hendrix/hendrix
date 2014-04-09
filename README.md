#Hendrix
###Twisted meets Django: *Making deployment easy*

Hendrix is a **multi-threaded**, **multi-process** *and* **asynchronous**
web server for *Django* projects. The idea here is to have a highly extensible
wsgi deployment tool that is fast, transparent and easy to use.

###Features
* **Multi-processing** - The WSGI app can be served from multiple 
processes on a single machine. Meaning that it can leverage multicore 
servers.
* **Resource Caching** - Process distributed resource caching, dynamically serving 
gzipped files. It's also possible to extend the current caching functionality by
subclassing the hendrix `CacheService` and addint `HENDRIX_SERVICES` in your
Django settings file.
* **Built-in SSL** - SSL is also process distributed, just provide the options 
--priv /path/to/private.key and --cert /path/to/signed.cert to enable SSL
and process distributed TLS
* **Multi-threading from within Django** - Enables the use of Twisted's `defer` 
module and `deferToThread` and `callInThread` methods from within Django
* **Built-in Websockets Framework**

###Installation

`pip install -e git+git@github.com:hangarunderground/hendrix.git@master#egg=hendrix`

###Deployment/Usage

For help:

`hx -h` or `hx --help`

Starting a server with 4 processes (1 parent and 3 child processes):

`hx start project.settings ./wsgi.py -p 8888 -w 3`

Stoping that server:

`hx stop project.settings ./wsgi.py -p 8888`

Restarting a server:

`hx restart project.settings ./wsgi.py -p 8888 -w 3`

###Serving Static Files
Serving static files via **Hendrix** is optional but easy.

* Anywhere in your project create a module e.g. `resources.py` in the package `myapp`
* To that module add the following code:
```python
from hendrix.resources import DjangoStaticResource
StaticFilesResource = DjangoStaticResource('/abs/path/to/static/folder')
```

The above code associates the static files to the url "static" relative
to the root url i.e. www.mysite.com/static/. To specify your 
own relative url e.g. "media" in `resources.py` ...

```python
from hendrix.resources import DjangoStaticResource
StaticFilesResource = DjangoStaticResource('/abs/path/to/static/folder', 'media')
```
* In you settings file add:
```python
HENDRIX_CHILD_RESOURCES = (
    'myapp.resources.StaticFilesResource',
)
```
* That's it.


###Django Runserver Equivalent
Install **hendrix** in your project's INSTALLED_APPS list
```python
INSTALLED_APPS = (
    ...,
    'hendrix',
    ...
)
```
and then in your terminal run

```
python manage.py hendrix --settings myproject.settings
```
This will reload your server every time a change is made to a python file in
your project.

###Twisted
Twisted is what makes this all possible. Mostly. Check it out [here](https://twistedmatrix.com/trac/).




###Yet to come
* Ensure stability of current implementation of web sockets
* Create an option to disable caching
* Load Balancing
* tests...


###History
It started as a fork of the
[slashRoot deployment module](https://github.com/SlashRoot/WHAT/tree/44f50ee08c5d7acb74ed8a4ce928e85eb2dc714f/deployment).

The name is the result of some inane psychological formula wherein the
'twisted' version of Django Reinhardt is Jimi Hendrix.

Hendrix is currently maintained by [Reelio](reelio.com).
