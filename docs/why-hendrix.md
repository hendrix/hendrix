## I'm making my website with python (say, Django or Pyramid).  Why do I need hendrix?

Python web frameworks (unlike, for example, node.js) are generally not an "all-in-one" solution for creating a live, production-capable web application.

Instead, most Python web frameworks depend on a server framework to actually deliver their content over the wire to your users.  The protocol of consensus for this exchange is WSGI (Web Server Gateway Interface - one of the most generic and useless protocol names in the history of network traffic).

So, hendrix implements WSGI to execute the logic of your web application.  Other projects that do exactly this are [mod_wsgi](https://modwsgi.readthedocs.org), [uWSGI](https://uwsgi-docs.readthedocs.org), and [gunicorn](http://gunicorn-docs.readthedocs.org).

These other projects are focused on some combination of being lightweight and unencumbered by dependencies.

This is where hendrix differs - it relies on Twisted, one of the best network engines ever written.  Twisted, though, adds some dependencies and heft.

In exchange for carrying a longer list of larger dependencies, hendrix brings to the table the character of being fundamentally, natively asynchronous.  It has easy-to-use and easy-to-test APIs for integrating many of the most awesome features of twisted directly in your python web application.


