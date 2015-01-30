# Quickstart

## The hx command

The simplest way to start hendrix for a Django project is to run the following command from the root of the project (ie, where manage.py is or was):

```bash
hx start --dev
```

The '--dev' option simply causes hendrix to emit output and elicit behavior similar to the Django runserver:

* '--reload' is implied: changes to the code will trigger reload
* '--loud' is implied: stdout and stderr will emit directly
* '--daemonize' is  disabled: the process will run in foreground of the currenty TTY.

## hendrix As a "service"

To install hendrix as a system service, you'll need to create hendrix.conf (See example below) and run the following.

```bash
sudo install-hendrix-service /path/to/hendrix.conf
```
hendrix.conf is is YAML format.  Here's an example.

```bash
# path to virtualenv
virtualenv: /home/anthony/venvs/hendrix

#path to manage.py
project_path: /home/anthony/django/myproject

#### everything below is optional #####
# settings, if you use different ones for production
settings: 'dot.path.to.settings'

# default 1
processes: 1

# default 8000
http_port: 8000

# default false
cache: false

# default 8080
cache_port: 8888

# default 4430
https_port: 4430

# key and cacert are both required if you want to run ssl
key: /path/to/my/priv.key
```

Then, to start the service.

```bash
sudo service hendrix start|stop
```
You may want to use something like supervisor, systemd, or upstart to launch hendrix on your remote metal.

Hendrix [ships with an upstart template](https://github.com/hangarunderground/hendrix/blob/master/hendrix/utils/templates/upstart.conf.j2) for this purpose; it can easily be modified to work with other similar services.

## Hendrix From Python
Launching your application from within your Python codebase, whether in your local development debugger or in the orchestration logic for your production fleet, can be an empowering and eye-opening experience.

Pythonic launch logic is an area where hendrix shines:

```
from hendrix.deploy.base import HendrixDeploy

options = {'settings': 'settings.location'}
deployer = HendrixDeploy(options=options)
deployer.run()
```

Now you have a logical place to put a breakpoint, emit a log entry, or [attach other services](deploying-other-services.md) that you might want to deploy.
