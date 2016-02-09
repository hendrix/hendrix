## History

In 2010, the landscape of options for offbeat network traffic in Python web applications were something like zero.  However, standing in stark contrast to this void of options was Twisted - arguably the most elegant and complete open source network engine ever created.

By way of a basic "hello world," a small group of tech activists at slashRoot, an upstate-NY technology collective, sought to simply build a web application capable of sending X10 signals to turn on or turn off the heat-lamp on the enclosure of a pet Python, Isis.

The X10 signal blocked for about 4 seconds, so it was inconvenient to do this during the request-response part of a web stream.

We asked [a question](http://stackoverflow.com/questions/4310706/django-comet-push-least-of-all-evils) or [two](http://stackoverflow.com/questions/4363899/making-moves-w-websockets-and-python-django-twisted) on StackOverflow, but were largely met with answers that failed to live up to the quality we expected from the Python ecosystem.

Enter Twisted, which, after some configuration, this process became both easy and performant.  In the years since that time, Twisted has enjoyed a resurgence in maintenance and feature richness.  Today, it is arguably the single finest Python package.

It is disheartening, albeit understandable, that Twisted hasn't become the de facto server for python web projects.  To truly make an environment out of Twisted that is easy, practical, and performant for most typical web cases is an undertaking which requires both a substantial dive into Twisted and a fair amount of code.

We submit that hendrix is the natural conclusion of such an undertaking.

In 2013, when Justin started working on the [Reelio](reelio.com) project, he brought with him the [slashRoot deployment module](https://github.com/SlashRoot/WHAT/tree/44f50ee08c5d7acb74ed8a4ce928e85eb2dc714f/deployment).  After a relatively short deliberation about what a "Twisted" version of Django Reinhardt might be, the name was settled.
