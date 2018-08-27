from twisted.conch.telnet import TelnetTransport, TelnetProtocol
from twisted.internet.protocol import ServerFactory

from hendrix.deploy.base import HendrixDeploy
from hendrix.experience import hey_joe


class TelnetToWebsocket(TelnetProtocol):

    def dataReceived(self, data):
        hey_joe.send('noodly_messages', data)


deployer = HendrixDeploy(options={'wsgi': 'hendrix_demo.wsgi.application', 'http_port': 7575})

websocket_service = hey_joe.WebSocketService("127.0.0.1", 9000)
deployer.add_non_tls_websocket_service(websocket_service)

telnet_server_factory = ServerFactory()
telnet_server_factory.protocol = lambda: TelnetTransport(TelnetToWebsocket)
deployer.reactor.listenTCP(6565, telnet_server_factory)

deployer.run()
