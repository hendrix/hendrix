![hendrix](_static/hendrix-logo.png)

**A complete wire harness for your python web app.**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(ie, handles bytes-on-the-wire to and from your Django thing or whatever)

## Overview

Python has wonderful web technologies and solutions for exposing web applications as network resources, such as uWSGI and Gunicorn.

Hendrix seeks to add to this discussion by focusing on:

* Being more feature-rich instead of more lightweight
* Being implemented more fully instead of more simply
* Adopting an agnosticism about WSGI and web applications

More about the hendrix philosophy [here](philosophy.md).

## Drawbacks

* Because hendrix relies on parts of Twisted that are not compatible with Python 3, hendrix is not yet Python 3-ready for many use cases.
* For many comparable situations, Hendrix likely uses more RAM and CPU than lighter-weight Python web servers.

## Getting started

See the [Quickstart](quickstart.md) or [FAQ](faq.md).
