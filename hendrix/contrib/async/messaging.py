
import json
import uuid

class RecipientManager(object):
    """
        This class manages all the transports addressable by a single address.

    """

    def __init__(self, transport, address):
        self.address = address
        self.transports = {}

        if transport is not None:
            self.transports[transport.uid] = transport


    def __repr__(self):

        return 'RecipientManager object at %s with %d recipients'%(self.address,len(self.transports))


    def add(self, transport):
        """
            add a transport
        """
        self.transports[transport.uid] = transport


    def send(self, string): #usually a json string...
        """
            sends whatever it is to each transport
        """
        for transport in self.transports.values():
            transport.write(string)

    def remove(self, transport):
        """
            removes a transport if a member of this group
        """
        if transport.uid in self.transports:
            del(self.transports[transport.uid])


class MessageDispatcher(object):

    def __init__(self, *args, **kwargs):
        self.recipients = {}


    def add(self, transport, address=None):
        """
            add a new recipient to be addressable by this MessageDispatcher
            generate a new uuid address if one is not specified
            
            reply to the transport with a "setup_connection" notice 
            containing the recipient's address for use as a return address 
            in such activities as form submission where a notification of 
            future results may be desired.
        """

        if not address:
            address = str(uuid.uuid1())

        if address in self.recipients:
            self.recipients[address].add(transport)
        else:
            self.recipients[address] = RecipientManager(transport, address)

        return address

    def remove(self, transport):
        """
            removes a transport from all channels to which it belongs.

        """
        for recManager in self.recipients.values():
            recManager.remove(transport)


    def send(self, address, data_dict):

        """
            address can either be a string or a list of strings
            
            data_dict gets sent along as is and could contain anything
            

        """
        if type(address) == list:
            recipients = [self.recipients.get(rec) for rec in address]
        else:
            recipients = [self.recipients.get(address)]

        # print 'recipients for message:', recipients

        if recipients:               
            for recipient in recipients:
                if recipient:
                    recipient.send(json.dumps(data_dict))

    
    def do_action(self, transport, data):
        """
            receives a dictionary.  cleans the input and tries to perform
            the appropriate action

        """

        actions = {
            'subscribe': self.subscribe
        }

        action = data.get('action')
        
        if action in actions:
            actions[action](transport, data)


    def subscribe(self, transport, data):
        """
            adds a transport to a channel
        """

        if 'address' in data:
            self.add(transport, data.get('address'))


def send_json_message(address, message, **kwargs):
    """
        a shortcut for message sending
    """

    data = {
        'message':message, 
        }

    data.update(kwargs)

    hxdispatcher.send(address, data)


def send_callback_json_message(value, *args, **kwargs):
    """
        useful for sending messages from callbacks as it puts the
        result of the callback in the dict for serialization
    """

    if value:
        kwargs['result'] = value

    send_json_message(args[0], args[1], **kwargs)

    return value


hxdispatcher = MessageDispatcher()

