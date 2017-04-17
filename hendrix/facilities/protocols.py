import sys
from twisted.internet import protocol

if sys.platform=='win32':
    from twisted.internet.iocpreactor.tcp import Server
else:
    from twisted.internet.unix import Server

class DeployServerProtocol(Server):
    """
    A process protocol for interprocess communication between
    HendrixDeploy and its workers.
    """

    def __init__(self):
        pass
