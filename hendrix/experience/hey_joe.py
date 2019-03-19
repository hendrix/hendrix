import json
import uuid

from collections import defaultdict
from itertools import chain

from twisted.internet import threads
from autobahn.twisted import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.logger import Logger

from hendrix.contrib.concurrency.signals import USE_DJANGO_SIGNALS


class _ParticipantRegistry(object):
    """
    A basic registry for our PubSub pattern - tracks topics and the participants who wish to receive messages for them.
    """
    log = Logger()

    def __init__(self):
        self._participants_by_topic = defaultdict(set)

    def _send(self, payload, participant):
        return participant.sendMessage(json.dumps(payload).encode())

    def _send_to_multiple_participants(self, payload, participants):
        # TODO: Optionally do this concurrently?
        for participant in participants:
            self._send(payload, participant)

    def send_to_topic(self, payload, topic):
        if type(topic) == list:
            recipients = chain(self._participants_by_topic[rec] for rec in topic)
        else:
            recipients = self._participants_by_topic[topic]
        payload_with_topic = (topic, payload)
        if not recipients:
            self.log.info("Nobody is subscribed to {}.".format(topic))
        else:
            return self._send_to_multiple_participants(payload_with_topic, recipients)

    def send_to_participant(self, payload, participant):
        payload_for_you = ("YOU", payload)
        self._send(payload_for_you, participant)

    def subscribe(self, transport, topic):
        if topic in ("YOU", "BROADCAST", "SUBSCRIBED", "UNSUBSCRIBED"):
            raise ValueError(
                """Can't subscribe to ("YOU", "BROADCAST", "SUBSCRIBED", "UNSUBSCRIBED") - these are reserved names.""")
        try:
            # Typically, the protocol is wrapped (as with TLS)
            participant = transport.wrappedProtocol
        except AttributeError:
            participant = transport.protocol
            # It's also possible to use a naked protocol.
        self._participants_by_topic[topic].add(participant)
        return participant

    def broadcast(self, payload):
        payload = ("BROADCAST", payload)
        self._send_to_multiple_participants(payload, self._all_participants())

    def _all_participants(self):
        return chain(*self._participants_by_topic.values())

    def remove(self, participant):
        """
        Unsubscribe this participant from all topic to which it is subscribed.
        """
        for topic, participants in list(self._participants_by_topic.items()):
            self.unsubscribe(participant, topic)
            # It's possible that we just nixe the last subscriber.
            if not participants:  # IE, nobody is still listening at this topic.
                del self._participants_by_topic[topic]

    def unsubscribe(self, participant, topic):
        return self._participants_by_topic[topic].discard(participant)


class _WayDownSouth(WebSocketServerProtocol):
    guid = None
    subscription_followups = {}

    def __init__(self, allow_free_redirect=False, subscription_message=None, registry=None, *args, **kwargs):
        self.subscription_message = subscription_message or "hx_subscribe"
        self.allow_free_redirect = allow_free_redirect
        self._registry = registry or _internal_registry
        super(_WayDownSouth, self).__init__(*args, **kwargs)

    def onMessage(self, payload_as_json, isBinary):
        # Extract json data
        payload = json.loads(payload_as_json.decode())

        # Signal Django
        if USE_DJANGO_SIGNALS:
            from ..contrib.concurrency.resources import send_django_signal
            threads.deferToThread(send_django_signal, None, payload)

        subscription_topic = payload.get(self.subscription_message)
        if subscription_topic:
            try:
                subscriber = self._registry.subscribe(self.transport, subscription_topic)
            except ValueError as e:
                # They tried to subscribe to a reserved word.
                return
            else:
                self.follow_up_subcription(subscription_topic, subscriber)

        if self.allow_free_redirect:
            if 'address' in payload:
                address = payload['address']
            else:
                address = self.guid

            self._registry.send(address, payload)

    def onOpen(self):
        self.guid = str(uuid.uuid1())

    def onClose(self, wasClean, code, reason):
        super(_WayDownSouth, self).onClose(wasClean, code, reason)
        self._registry.remove(self.transport)

    def follow_up_subcription(self, topic, participant):
        try:
            followup = self.subscription_followups[topic]
            followup(participant)
        except KeyError:
            # Default follow-up - just confirm their subscription.
            self.sendMessage("Subscribed to {}".format(topic).encode())


class WebSocketService(WebSocketServerFactory):
    prefix = "ws"

    def __init__(self, host_address, port, *args, **kwargs):
        # Note: You can pass a test reactor here a as a kwarg; the parent objects will respect it.
        self._hey_joe_addr = "{}://{}:{}".format(self.prefix, host_address, port)
        super(WebSocketService, self).__init__(self._hey_joe_addr, *args, **kwargs)
        self.protocol = _WayDownSouth
        self.server = "hendrix/Twisted/" + self.server

    def register_followup(self, topic, followup):
        self.protocol.subscription_followups[topic] = followup


class WSSWebSocketService(WebSocketService):
    """
    Websocket service that uses the Autobahn TLS behavior to create a WSS service.
    """
    prefix = "wss"

    def __init__(self, host_address, port, allowedOrigins, *args, **kwargs):
        super(WSSWebSocketService, self).__init__(host_address, port, *args, **kwargs)
        self.setProtocolOptions(allowedOrigins=allowedOrigins)


# The main singleton instance to use with the subsequent classes here.
# (omg, did we just make a stateful HTTP service?  Nobody tell IETF.)
_internal_registry = _ParticipantRegistry()


def send(payload, topic=None, transport=None):
    if (topic is None and transport is None) or (topic and transport):
        raise ValueError("You must specify either a topic or a transport; not both.")
    if topic is not None:
        return _internal_registry.send_to_topic(payload, topic)
    elif transport is not None:
        return _internal_registry.send_to_transport(payload, transport)
    assert False


def broadcast(payload):
    return _internal_registry.broadcast(payload)
