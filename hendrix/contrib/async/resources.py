from twisted.internet.protocol import Factory, Protocol
from txsockjs.factory import SockJSResource
from .messaging import hxdispatcher

import json


class MessageHandlerProtocol(Protocol):
    """
        A basic protocol for socket messaging 
        using a hendrix messaging dispatcher to handle
        addressing messages to active sockets from
        differnt contexts
    """
    dispatcher = hxdispatcher
    guid = None

    def dataReceived(self, data):

        """
            Takes "data" which we assume is json encoded
            If data has a uid attribute, we pass that to the dispatcher
            as the message_id so it will get carried through into any 
            return communications and be identifiable to the client

            falls back to just passing the message along...

        """

        try:
            data = json.loads(data)
            self.dispatcher.send(self.guid, data, message_id=data.get('subject_id'))
        except:
            self.dispatcher.send(self.guid, {'message':data})

    def connectionMade(self):
        """
            establish the address of this new connection and add it to the list of 
            sockets managed by the dispatcher
        """
        self.guid = self.dispatcher.add(self.transport)


    def connectionLost(self, something):
        """
            clean up the no longer useful socket in the dispatcher
        """
        self.dispatcher.remove(self.guid)


def get_MessageHandler():
    """
        create an instance of the SockJSResource for use 
        as a child to the main wsgi app
    """

    return SockJSResource(Factory.forProtocol(MessageHandlerProtocol))
