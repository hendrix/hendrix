![hendrix](_static/hendrix-logo.png)

**A complete wire harness for your python web app.**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(ie, handles bytes-on-the-wire to and from your Django thing or whatever)

Python has wonderful web technologies and solutions for exposing web applications and network resources, such as mod_wsgi, uWSGI and Gunicorn.

Hendrix seeks to add to this discussion by focusing on:

* Being async-native and providing "web culture" APIs for doing "async stuff."
* Being more feature-rich instead of more lightweight
* Adopting an agnosticism about the status of WSGI and web applications as network services

More about the hendrix philosophy [here](philosophy.md).

## Drawbacks

* Because hendrix relies on parts of Twisted that are not compatible with Python 3, hendrix is not yet Python 3-ready for many use cases.
* For many comparable situations - especially the simple synchornous/ blocking scenario, Hendrix likely uses more RAM and CPU than lighter-weight Python web servers.

## Getting started

See the [Quickstart](quickstart.md) or [FAQ](faq.md).

## History
It started as a fork of the
[slashRoot deployment module](https://github.com/SlashRoot/WHAT/tree/44f50ee08c5d7acb74ed8a4ce928e85eb2dc714f/deployment).

The name is the result of some inane psychological formula wherein the
'twisted' version of Django Reinhardt is Jimi Hendrix.

Hendrix is currently maintained by [Reelio](reelio.com).
