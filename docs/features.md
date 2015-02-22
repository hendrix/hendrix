#Features in more depth

## Static Files
Serving static files via **Hendrix** is optional but easy.


A default static file handler is built into Hendrix which can be used by adding the following to your settings:
```python
HENDRIX_CHILD_RESOURCES = (
  'hendrix.contrib.resources.static.DefaultDjangoStaticResource',

  # uncomment if you would like to serve the django admin static files
  #'hendrix.contrib.resources.static.DjangoAdminStaticResource',
  )
  ```
  No other configuration is necessary.  You don't need to add anything to urls.py.

  You can also easily create your own custom static or other handlers by adding them to ```HENDRIX\_CHILD\_RESOURCES```.


## SSL
This is made possible by creating a self-signed key. First make sure you have
the newest **patched** version of openssl.
Then generate a private key file:
```bash
$ openssl genrsa > key.pem
```
Then generate a self-signed SSL certificate:
```bash
$ openssl req -new -x509 -key key.pem -out cacert.pem -days 1000
```

Finally you can run single SSL server by running:
```bash
$ hx start --dev --key key.pem --cert cacert.pem
```
or a process distributed set of SSL servers:
```bash
hx start --dev --key key.pem --cert cacert.pem -w 3
```
Just go to `https://[insert hostname]:4430/` to check it out.
N.B. Your browser will warn you not to trust the site... You can also specify
which port you want to use by passing the desired number to the `--https_port`
option


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

## Testing

In your virtualenv first run the following:

pip install -r requirements
pip install -r test-requirements

Tests live in `hendrix.test` and are most easily run using Twisted's
[trial](https://twistedmatrix.com/trac/wiki/TwistedTrial) test framework.
```bash
/home/jsmith:~$ trial hendrix
hendrix.test.test_deploy
DeployTests
test_multiprocessing ...                                               [OK]
test_options_structure ...                                             [OK]
test_settings_doesnt_break ...                                         [OK]

-------------------------------------------------------------------------------
Ran 3 tests in 0.049s

PASSED (successes=3)
```
**trial** will find your tests so long as you name the package/module such that
it starts with "test" e.g. `hendrix/contrib/cache/test/test_services.py`.

Note that the module needs to have a subclass of unittest.TestCase via the expected
unittest pattern. For more info on *trial* go [here](https://twistedmatrix.com/trac/wiki/TwistedTrial).

N.B. that in the `hendrix.test` `__init__.py` file a subclass of TestCase
called `HendrixTestCase` has been created to help tests various use cases
of `hendrix.deploy.HendrixDeploy`
