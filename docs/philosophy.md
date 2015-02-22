#Philosphy

### Your WSGI app is just another network resource, and ports 80 and 443 are just ports.

The simplest use case for Hendrix is to launch your Django app in a typical and well-established way.  However, once your app is handed over to Twisted, it is treated like just another network resource.  

One of the best and most obvious ways to take advantage of this disposition is to [integrate other services](deploying-other-services.md) into your hendrix application.

Your web app doesn't have to be a WSGI app as we know it, Jim - it can also be a pub/sub server, connect to an IRC server, or emit raw ethernet frames!

### Sharing launch logic between all of your environments, from development to production, is pretty good.



### Don't do with a message queue what rightly belongs in a thread or process - and vice-versa.
