## Why the name?

Django Reinhardt is the incredible innovative guitarist after whom the web framework Django is named.  Imagine now a strange, Twisted version of Django Reinhardt; still recognizable, but now busy, frizzy, and electric.


## Why another Python server?

Gunicorn and uWSGI are great at what they do: listen on a port for requests and pass those requests on to a WSGI app.

Instead of being first-and-foremost a WSGI container, Hendrix is first-and-foremost a network engine - a Twisted application.

As such, Hendrix is natively able to do threading, asynchrony, websocket traffic, and [speak directly to other services](deploying-other-services.md) in your architecture.
 

## Wait, async with Django?  How have you solved the problem of the (ORM, Template Loader, etc) blocking?

This is one of the first questions people ask when they start to get interested.

No, hendrix doesn't just haphazardly call async logic from your Django app.  Instead, it contains the Django app in Twisted.  This way, the Django app can't block the reactor.

In other words, each request-response cycle remains synchronous; Django believes it is running in a blocking environment at all times.
