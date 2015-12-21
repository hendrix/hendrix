from twisted.internet import protocol
from twisted.internet.unix import Server

class DeployServerProtocol(Server):
    """
    A process protocol for interprocess communication between
    HendrixDeploy and its workers.
    """

    def __init__(self, args):
        self.args = args

    def connectionMade(self):
        self.transport.write(self.args)
        self.transport.closeStdin()
