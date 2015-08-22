# Philosophy

### Your WSGI app is just another network resource, and ports 80 and 443 are just ports.

The simplest use case for Hendrix is to launch your Django app in a typical and well-established way.  However, once your app is handed over to Twisted, it is treated like just another network resource.  

One of the best and most obvious ways to take advantage of this disposition is to [integrate other services](deploying-other-services.md) into your hendrix application.

Your web app doesn't have to be a WSGI app as we know it, Jim - it can also be a pub/sub server, connect to an IRC server, or emit raw ethernet frames!

### Sharing launch logic between all of your environments, from development to production, is pretty good.

It's still sadly normal to use "mange.py runserver" in development and then something completely different in staging and production environments.

Why?!

If you're using hendrix, it's almost certain that you'll use the exact same logic to launch your app in your development environment as you will on a production host - namely, import HendrixDeploy and call it.


### Don't do with a message queue what rightly belongs in a thread or process - and vice-versa.

When a python web project is ready to add even fairly mundane asynchrony, an all-too-common solution is to immediately warp way ahead and install the various components of a message queue solution, slapping Celery and a broker such as RabbitMQ (and sometimes also redis) over the web logic.  

For all but the most mature projects, this usually represents the biggest infrastructural change the project will have undertaken to date.  You've got your team learning gevent.  You're re-thinking the layout of most of your web views.  You're using the @task decorator in ways that you aren't sure make sense ("isn't everything a task?" is a question you're hearing in casual conversation).

Even if this process were easy, cheap, and fast - and it's usually none of those - it's simply the wrong solution to the problem.  

If you literally want to do more than one thing at the same time in Python, the proper ways to do so are with a separate thread (which will split resources away from the current process) or with a separate process (which can occur on the same server resource or a different one). 

Message queues are a sweet technology and they have a place.  When you want to maintain a replicable, introspective list of outstanding jobs,  modeled and managed in the shape and character of a "to do" list, nothing beats a message queue.

If you follow the orthodoxy described above, then by the time you actually *need* a message queue, your message queue solution will already be polluted by features that were better served by true asynchrony.

And in the near term, when what you want is to literally do more than one thing at the same time, a message queue adds unnecessary complexity, a bunch of moving parts, and obscure performance tuning.

A better first foray into asynchrony is the [crosstown_traffic](crosstown_traffic.md) API.  Give it a look and see if you still want to rush to install Celery.

### Drawbacks to hendrix

* Because hendrix relies on parts of Twisted that are not compatible with Python 3, hendrix is not yet Python 3-ready for many use cases.
* For many comparable situations - especially the simple synchornous/ blocking scenario, Hendrix likely uses more RAM and CPU than lighter-weight Python web servers such as uWSGI.

