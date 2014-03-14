from twisted.internet.protocol import Factory, Protocol
from txsockjs.factory import SockJSResource
from .messaging import hxdispatcher

import json


class MessageHandlerProtocol(Protocol):
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
            establish the address of this 
        """
        self.guid = self.dispatcher.add(self.transport)


    def connectionLost(self, something):
        # print 'connection lost:',something
        self.dispatcher.remove(self.guid)


def get_MessageHandler():
    return SockJSResource(Factory.forProtocol(MessageHandlerProtocol))
