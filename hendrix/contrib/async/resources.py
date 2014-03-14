from twisted.internet.protocol import Factory, Protocol
from txsockjs.factory import SockJSResource
from .messaging import hxdispatcher

import json


class MessageHandlerProtocol(Protocol):

    guid = None

    def dataReceived(self, data):
        try:
            data = json.loads(data)
            hxdispatcher.send(self.guid, data, message_id=data.get('uid'))
        except:
            pass



        # uid = str(uuid.uuid1())

        # send_json_message(self.transport, uid,
        #                   message='ok, starting complicated background task...')
        # deferToThread(ReturnWhenFinished, self.transport,
        #               data, random.random() * float(10), uid)

    def connectionMade(self):
        self.guid = hxdispatcher.add(self.transport)


    def connectionLost(self, something):
        # print 'connection lost:',something
        hxdispatcher.remove(self.guid)


def get_MessageHandler():
    return SockJSResource(Factory.forProtocol(MessageHandlerProtocol))
