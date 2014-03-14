# from txrdq.rdq import ResizableDispatchQueue

from twisted.internet.threads import deferToThread

from .signals import short_task
from .messaging import send_callback_json_message


def errorHandler(failure):

    print failure
    # failure.trap(SpamException, EggException)
    # Handle SpamExceptions and EggExceptions

def print_hello():
    print 'hello'


def process_short_task(args):

    print 'starting %r with args %r and kwargs %r' % (args[0], args[1], args[2])

    func = args[0]
    func_args = args[1]

    print func_args[0]


    func_kwargs = args[2]

    func(*func_args, **func_kwargs)


# SHORT_JOB_QUEUE = ResizableDispatchQueue(process_short_task, 5)

def send_short_task(sender, *args, **kwargs):

    args = kwargs['args']
    
    func = args[0]
    args = args[1:][0]
    kwargs = kwargs['kwargs']


    rec = kwargs.pop('hxrecipient')
    mess = kwargs.pop('hxmessage')


    print func
    print args
    print kwargs

    job = deferToThread(func, *args, **kwargs)

    job.addCallback(send_callback_json_message, rec, mess)



short_task.connect(send_short_task, dispatch_uid="hendrix.queue_short_task")
print 'connected signals'

