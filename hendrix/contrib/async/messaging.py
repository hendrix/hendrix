
import json

import uuid





class RecipientInfo(object):

    def __init__(self, transport, uid=None):
        self.transport = transport

        if not uid:
            uid = str(uuid.uuid1())
        self.last_message_id = uid


class MessageDispatcher(object):

    def __init__(self, *args, **kwargs):
        self.recipients = {}

    def add(self, transport, address=None):

        if not address:
            address = str(uuid.uuid1())

        self.recipients[address] = RecipientInfo(transport)
        self.send(address, {'setup_connection':address})

        return address

    def remove(self, address):
        del(self.recipients[address])


    def send(self, address, data_dict, subject_id=None):

        recipient = self.recipients.get(address)

        if not subject_id:
            subject_id = recipient.last_message_id
        
        recipient.last_message_id = subject_id

        data_dict.update({'subject_id':subject_id})

        recipient.transport.write(json.dumps(data_dict))


hxdispatcher = MessageDispatcher()




def send_json_message(address, message, **kwargs):

    data = {
        'message':message, 
        'clear': True
        }

    data.update(kwargs)

    hxdispatcher.send(address, data, subject_id=kwargs.get('subject_id'))


def send_callback_json_message(value, *args, **kwargs):

    if value:
        kwargs['result'] = value

    send_json_message(args[0], args[1], **kwargs)



