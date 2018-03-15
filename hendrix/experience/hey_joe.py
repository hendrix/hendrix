import json
import uuid
from collections import defaultdict
from itertools import chain

from autobahn.twisted import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol


class _ParticipantRegistry(object):
    """
    A basic registry for our PubSub pattern - tracks topics and the transports who wish to receive messages for them.
    """
    def __init__(self):
        self._transports_by_topic = defaultdict(list)

    def add(self, transport, topic=None):
        if not topic:
            topic = str(uuid.uuid1())
        self._transports_by_topic[topic].append(transport)
        return topic

    def remove(self, transport):
        for topic, recipients in list(self._transports_by_topic.items()):
            recipients.remove(transport)
            if not recipients:  # IE, nobody is still listening at this topic.
                del self._transports_by_topic[topic]

    def send(self, topic, data_dict):
        """
        topic can either be a string or a list of strings

        data_dict gets sent along as is and could contain anything
        """
        if type(topic) == list:
            recipients = chain(self._transports_by_topic.get(rec) for rec in topic)
        else:
            recipients = self._transports_by_topic.get(topic)

        if recipients:
            for recipient in recipients:
                if recipient:
                    recipient.protocol.sendMessage(json.dumps(data_dict).encode())

    def subscribe(self, transport, topic):
        self.add(transport=transport, topic=topic)

        self.send(
            topic,
            {'message': "%r is listening" % transport}
        )

# The main singleton instance to use with the subsequent classes here.
_registry = _ParticipantRegistry()


class _WayDownSouth(WebSocketServerProtocol):

    def __init__(self, allow_free_redirect=False, subscription_message=None, *args, **kwargs):
        self.subscription_message = subscription_message or "hx_subscribe"
        self.allow_free_redirect = allow_free_redirect
        super(_WayDownSouth, self).__init__(*args, **kwargs)

    def onConnect(self, request):
        super(_WayDownSouth, self).onConnect(request)
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        super(_WayDownSouth, self).onOpen()
        print("WebSocket connection open.")

    def connectionMade(self, *args, **kwargs):
        super(_WayDownSouth, self).connectionMade(*args, **kwargs)
        self.transport.uid = str(uuid.uuid1())

        self.guid = _registry.add(self.transport)
        _registry.send(self.guid, {'setup_connection': self.guid})

    def onMessage(self, payload_as_json, isBinary):

        try:
            payload = json.loads(payload_as_json.decode())

            subscription_topic = payload.get(self.subscription_message)
            if subscription_topic:
                _registry.subscribe(self.transport, subscription_topic)

            if self.allow_free_redirect:
                if 'address' in payload:
                    address = payload['address']
                else:
                    address = self.guid

            self._dispatcher.send(address, payload)

        except Exception as e:
            raise
            self._dispatcher.send(
                self.guid,
                {'message': payload, 'error': str(e)}
            )

    def onClose(self, wasClean, code, reason):
        super(_WayDownSouth, self).onClose(wasClean, code, reason)
        _registry.remove(self.transport)
        print("WebSocket connection closed: {0}".format(reason))


class WebSocketService(WebSocketServerFactory):

    def __init__(self, host_address, port, *args, **kwargs):
        # Note: You can pass a test reactor here a as a kwarg; the parent objects will respect it.
        self._hey_joe_addr = "ws://{}:{}".format(host_address, port)
        super(WebSocketService, self).__init__(self._hey_joe_addr, *args, **kwargs)
        self.protocol = _WayDownSouth
        self.server = "hendrix/Twisted/" + self.server


def send(address, data_dict):
    return _registry.send(address, data_dict)
