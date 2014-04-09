#Hendrix
###Twisted meets Django: *Making deployment easy*

Hendrix is a **multi-threaded**, **multi-process** *and* **asynchronous**
web server for *Django* projects. The idea here is to have a highly extensible
wsgi deployment tool that is fast, transparent and easy to use.

###Installation

`pip install -e git+git@github.com:hangarunderground/hendrix.git@master#egg=hendrix`

###Deployment

Starting a server with 4 processes (1 parent and 3 child processes):

`hx start project.settings ./wsgi.py -p 8888 -w 3`

Stoping that server:

`hx stop project.settings ./wsgi.py -p 8888`

Restarting a server:

`hx restart project.settings ./wsgi.py -p 8888 -w 3`

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
* Does adding services to child processes yield duplicate behaviour
* SSLServer
* tests...


###History
It started as a fork of the
[slashRoot deployment module](https://github.com/SlashRoot/WHAT/tree/44f50ee08c5d7acb74ed8a4ce928e85eb2dc714f/deployment).

The name is the result of some inane psychological formula wherein the
'twisted' version of Django Reinhardt is Jimi Hendrix.

Hendrix is currently maintained by [Reelio](reelio.com).
