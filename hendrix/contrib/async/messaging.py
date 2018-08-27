import copy
import json
import uuid

import warnings

warnings.warn("hendrix.contrib.concurrency.messaging is being deprecated.  Use hendrix.experience.hey_joe instead.",
              DeprecationWarning)


class RecipientManager(object):
    """
        This class manages all the transports addressable by a single address.
    """

    def __init__(self, transport, address):
        self.address = address
        self.transports = {}

        if transport is not None:
            self.add(transport)

    def __repr__(self):
        return 'RecipientManager object at %s with %d recipients' % (
            self.address, len(self.transports)
        )

    def add(self, transport):
        """
            add a transport
        """
        self.transports[transport.uid] = transport

    def send(self, message):  # usually a json string...
        """
            sends whatever it is to each transport
        """
        for transport in self.transports.values():
            transport.protocol.sendMessage(message)

    def remove(self, transport):
        """
            removes a transport if a member of this group
        """
        if transport.uid in self.transports:
            del (self.transports[transport.uid])


class MessageDispatcher(object):
    """
    MessageDispatcher is a PubSub state machine that routes data packets
    through an attribute called "recipients". The recipients attribute is a
    dict structure where the keys are unique addresses and the values are
    instances of RecipientManager. "address"es (i.e. RecipientManagers) are
    created and/or subscribed to. Subscribing to an address results in
    registering a clientswebsocket (i.e. the transport associated to the
    SockJSResource protocol) within a dict that is internal to the Manager
    called "transports".
    RecipientManager's purpose is to expose functions that MessageDispatcher
    can leverage to execute the PubSub process.
    N.B. subscribing a client to an address opens that client to all data
        published to that address. As such it useful to think of addresses as
        channels. To acheive a private channel an obsure address is required.
    """

    def __init__(self, *args, **kwargs):
        self.recipients = {}

    def add(self, transport, address=None):
        """
            add a new recipient to be addressable by this MessageDispatcher
            generate a new uuid address if one is not specified
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
        recipients = copy.copy(self.recipients)
        for address, recManager in recipients.items():
            recManager.remove(transport)
            if not len(recManager.transports):
                del self.recipients[address]

    def send(self, address, data_dict):

        """
            address can either be a string or a list of strings

            data_dict gets sent along as is and could contain anything
        """
        if type(address) == list:
            recipients = [self.recipients.get(rec) for rec in address]
        else:
            recipients = [self.recipients.get(address)]

        if recipients:
            for recipient in recipients:
                if recipient:
                    recipient.send(json.dumps(data_dict).encode())

    def subscribe(self, transport, data):
        """
            adds a transport to a channel
        """

        self.add(transport, address=data.get('hx_subscribe').encode())

        self.send(
            data['hx_subscribe'],
            {'message': "%r is listening" % transport}
        )


def send_json_message(address, message, **kwargs):
    """
        a shortcut for message sending
    """

    data = {
        'message': message,
    }

    if not kwargs.get('subject_id'):
        data['subject_id'] = address

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


def send_errback_json_message(error, *args, **kwargs):
    kwargs['error'] = error.getErrorMessage()
    send_json_message(args[0], args[1], **kwargs)

    error.trap(RuntimeError)


hxdispatcher = MessageDispatcher()
