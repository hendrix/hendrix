from twisted.test.proto_helpers import StringTransportWithDisconnection

from hendrix.experience import hey_joe


def test_websocket_mechanics():
    """
    Shows that we can put our protocol (hey_joe._WayDownSouth) and factory (hey_joe.WebSocketService)
    together, along with a transport, and properly open a websocket connection.
    """
    transport = StringTransportWithDisconnection()
    service = hey_joe.WebSocketService("127.0.0.1", 9000)
    protocol = service.buildProtocol(service._hey_joe_addr)
    protocol.transport = transport
    transport.protocol = protocol
    protocol.connectionMade()
    data_to_send = b'GET / HTTP/1.1\r\nHost: somewhere_in_the_world:9000\r\nConnection: keep-alive, Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: F76ObkF/aCKX8WkmAgx2OQ==\r\n\r\n'
    protocol.dataReceived(data_to_send)
    assert transport.value().startswith(b'HTTP/1.1 101 Switching Protocols\r\nServer: hendrix')
