# from txrdq.rdq import ResizableDispatchQueue

from twisted.internet.threads import deferToThread
from django.dispatch import receiver

from .signals import short_task, long_task
from .messaging import send_callback_json_message, send_json_message, send_errback_json_message

import inspect


def parse_signal_args(kwargs):

    # because of the way django signals work, args will be in kwargs
    args = kwargs['args']

    # we have 2 arguments that we need to pull from the 'args' tuple
    func = args[0]  # the function we will be calling
    # args[1:][0] is a tuple...
    args = args[1:][0][0]

    # and then any keyword args
    kwargs = kwargs['kwargs']

    return func, args, kwargs


@receiver(short_task, dispatch_uid="hendrix.queue_short_task")
def send_short_task(sender, *args, **kwargs):
    """
        preps arguments which can come in many forms
        sendes them to a deferred thread with an optional
        callback to send results through a websocket (or other transport)
    """

    func, args, kwargs = parse_signal_args(kwargs)

    # specific args are used to address the message callback
    rec = kwargs.pop('hxrecipient', None)
    mess = kwargs.pop('hxmessage', None)
    subj = kwargs.pop('hxsubject_id', None)

    additional_callbacks = kwargs.pop('hxcallbacks', [])

    # send this job to a deferred thread
    job = deferToThread(func, *args, **kwargs)

    # and if we have a reciever, add the callback
    if rec:
        job.addCallback(send_callback_json_message, rec, mess, subject_id=subj)

        send_json_message(
            rec,
            'starting...',
            subject_id=subj,
            clear=True
        )

        job.addErrback(send_errback_json_message, rec, mess, subject_id=subj)

    for callback in additional_callbacks:
        job.addCallback(callback)


try:
    from celery import task
    import importlib

    @task
    def run_long_function(function_to_run, *args, **kwargs):
        print function_to_run, args, kwargs
        path_to_module, function_name = function_to_run.rsplit('.', 1)
        module = importlib.import_module(path_to_module)

        result = getattr(module, function_name)(*args, **kwargs)
        return result
except:
    pass


def task_complete_callback(celery_job_in_progress):

    return celery_job_in_progress.get()


@receiver(long_task, dispatch_uid="hendrix.queue_long_task")
def send_long_task(sender, *args, **kwargs):
    """
    preps arguments, sends to some kind of message queue backed task manager?
    sets up a callback which checks for the completion of this task and
    messages interested parties about its completion
    """
    # for external execution, we need to get the module path to the function

    func, args, kwargs = parse_signal_args(kwargs)

    module_name = inspect.getmodule(func).__name__
    func_name = func.__name__
    path_to_function = '%s.%s' % (module_name, func_name)

    # specific args are used to address the message callback
    rec = kwargs.pop('hxrecipient', None)
    mess = kwargs.pop('hxmessage', None)
    subj = kwargs.pop('hxsubject_id', None)
    additional_callbacks = kwargs.pop('hxcallbacks', [])

    try:
        # send this job to celery
        job = run_long_function.delay(path_to_function, *args, **kwargs)

        # create a deferred thread to watch for when it's done
        monitor = deferToThread(task_complete_callback, job)

        # tell someone that this happened?
        if rec:
            send_json_message(
                rec,
                'starting processing...',
                subject_id=subj,
                clear=True
            )
            # hook up notifiecation for when it's finished
            monitor.addCallback(
                send_callback_json_message, rec, mess, subject_id=subj
            )

        for callback in additional_callbacks:
            monitor.addCallback(callback)

        monitor.addErrback(
            send_errback_json_message, rec, mess, subject_id=subj
        )
    except Exception:
        raise NotImplementedError(
            "You must have celery installed and configured to queue long "
            "running tasks"
        )
