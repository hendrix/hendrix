import uuid

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.websocket.protocol import WebSocketProtocol
import json

from hendrix.contrib.async.messaging import hxdispatcher


class MyServerProtocol(WebSocketServerProtocol):

    dispatcher = hxdispatcher

    def __init__(self, *args, **kwargs):
        self.state = WebSocketProtocol.STATE_CLOSED
        super().__init__(*args, **kwargs)

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def connectionMade(self, *args, **kwargs):
        """
        establish the address of this new connection and add it to the list of
        sockets managed by the dispatcher

        reply to the transport with a "setup_connection" notice
        containing the recipient's address for use by the client as a return
        address for future communications
        """
        super().connectionMade(*args, **kwargs)
        self.transport.uid = str(uuid.uuid1())

        self.guid = self.dispatcher.add(self.transport)
        self.dispatcher.send(self.guid.encode(), {'setup_connection': self.guid})

    def dataReceived(self, data):

        """
            Takes "data" which we assume is json encoded
            If data has a subject_id attribute, we pass that to the dispatcher
            as the subject_id so it will get carried through into any
            return communications and be identifiable to the client

            falls back to just passing the message along...

        """

    def onMessage(self, payload, isBinary):

        try:
            address = self.guid
            json_payload = json.loads(payload.decode())
            # threads.deferToThread(send_signal, self.dispatcher, data)

            if 'hx_subscribe' in json_payload:
                return self.dispatcher.subscribe(self.transport, json_payload)

            if 'address' in json_payload:
                address = json_payload['address']
            else:
                address = self.guid

            self.dispatcher.send(address, json_payload)

        except Exception as e:
            raise
            self.dispatcher.send(
                self.guid,
                {'message': json_payload, 'error': str(e)}
            )

        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.dispatcher.remove(self.transport)
        print("WebSocket connection closed: {0}".format(reason))
