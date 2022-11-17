'''
Runs the test WSGI application on a real HendrixDeploy.

Useful for poking and prodding to discover how to cover those hard-to-reach
parts of the service flow.
'''

from twisted.internet import reactor

from hendrix.deploy.base import HendrixDeploy
from resources import application

if __name__ == "__main__":
    threadPool = reactor.getThreadPool()
    threadPool.adjustPoolsize(3, 5)
    options = {'wsgi': application}
    deployer = HendrixDeploy(options=options)
    deployer.run()
