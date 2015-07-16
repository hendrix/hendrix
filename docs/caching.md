##Caching

At the moment a caching server is deployed by default on port 8000. Is serves
gzipped content, which is pretty cool - right?

#####How it works

The Hendrix cache server is a reverse proxy that sits in front your Django app.
However, if you wanted to switch away from the cache server you can always point
to the http port (default 8080).

It works by forwarding requests to the http server running the app and
caches the response depending on the availability of `max-age` [seconds] in a
`Cache-Control` header.

#####Busting the cache

Note that you can bust the cache (meaning force it not to cache) by passing
a query in your GET request e.g. `http://somesite.com/my/resource?somevar=test`.
You can also force the query to cache by specifying `cache=true` in the query
e.g. `http://somesite.com/my/resource?somevar=test,cache=true` (so long as a
`max-age` is specified for the handling view).
What this means is that you can let the browser do some or none of the js/css
caching if you so want.

#####Caching in Django

In your project view modules use the `cache_control` decorator to add
a `max-age` of your choosing. e.g.

```python
from django.views.decorators.cache import cache_control

@cache_control(max_age=60*60*24)  # cache it for a day
def homePageView(request):
...
```

and that's it! Hendrix will do the rest. Django docs examples [here](https://docs.djangoproject.com/en/dev/topics/cache/#controlling-cache-using-other-headers)

#####Turning cache off

You can turn caching on by passing the flags `-c` or `--cache`. You can also change which
port you want to use with the `--cache_port` option.

#####Global Vs Local

If you're running multiple process using the `-w` or `--workers` options caching
will be process distributed by default. Meaning there will be a reverse proxy
cache server for each process. However if you want to run the reverse
proxy server on a single process just use the `-g` or `--global_cache` flags.

... here "local" means local to the process.
