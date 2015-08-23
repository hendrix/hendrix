# Crosstown Traffic Decorator

  @crosstown_traffic is a decorator that will defer logic inside a view until a specific phase in the response process and optionally run it on a different thread or threads.

For example, let's say we are building a REST endpoint that causes 100 phone calls to be placed via the twilio API.

We don't want to wait, obviously, until 100 API calls are made in order to send our response back to the client.

However, we want to make those calls as soon as we're done with what the user needs.

Here's the pattern for doing this with crosstown_traffic:


```python
def my_django_view(request):

    # Do some django stuff, decide that we need to do some stuff after the request is over (like place 100 phone calls via the Twilio API)

        for phone_call_logic in 100_phone_calls:

            # 100 phone calls, each on their own thread, but not starting until the response has gone out over the wire

            @crosstown_traffic()
            def place_100_phone_calls():
                phone_call_logic()

    # More django stuff, including ORM activity, which will resolve on this thread, before the crosstown_traffic begins.

      return HttpResponse('this is synchronous')

      # And only now that we've got the response out over the wire will place_100_phone_calls happen.
```
#### Threading
By default, crosstown_traffic will run the decorated callable on a new thread in the same threadpool as your app.

However, if you want to run it on the same thread (and thus block that thread from handling other requests until the callable is finished), you can use the same_thread kwarg:

```python
@crosstown_traffic(same_thread=True)
def thing_that_will_happen_after_response_on_same_thread():
    hopefully_short_thing()
```

#### Preventing execution by status code
By default, if your app responds with a 5xx or 4xx status code (a Server Error or Client Error), the crosstown_traffic for that response will NOT execute.

However, if you want to change these "no_go_status_codes" per callable, you can do so:

```python
@crosstown_traffic(no_go_status_codes=['5xx', '400-405', 302])
def long_thing():
    time.sleep(10)
    print '''
    Ten seconds ago, the server responded with a status code
    that was not in the 500's, was not 400-405, and was not 302.
    '''
```

### Why not just use deferToThread or callFromThread?

Twisted already has great APIs for running functions on separate threads or running programs as different processes - why does hendrix need an additional async API?

Here are the reasons that @crosstown_traffic is necessary, in ascending order of strength:

#### The syntax is cleaner

Consider the alternative syntax, which only almost accomplishes the same thing as the snippet above:

```python
def my_django_view(request):

    # Do some django stuff, decide that we need to do some stuff after the request is over (like place 100 phone calls via the Twilio API)

        for phone_call_logic in 100_phone_calls:

            # 100 phone calls, each on their own thread, beginning immediately

            def place_100_phone_calls():
                phone_call_logic()

        deferToThread(phone_call_logic)

    # And database stuff may still be occuring.

    return HttpResponse('this is synchronous')
```

Obviously the syntax is similar, and there are surely use cases for this exact deferToThread pattern.

However, if place_100_phone_calls is more than a few lines long, the reader will be left in suspense about the matter of when to expect execution.  For an ordinary blocking web view, this might not be a big deal.  But when the logic will be executed asynchronously on a different thread, at a different time, with a different application state, it's totally reasonable to clarify that up front.

So, by contrast, the crosstown_traffic syntax of "treat this function pursuant to this decorator logic" puts the logic intention at the top, rather than the bottom, of the block.  In this sense, it is also similar to the @route decorator from Flask or the @detail_route decorator from Django-Rest-Framework.

#### It's far simpler to test in the Django test runner

Generally, testing asynchronous logic in the Django test runner is a pain point.  This, for example, is the reason that Celery-based projects nearly always have the CELERY_ALWAYS_EAGER setting set to True in their test suite.

Consider that such a configuration fundamentally changes the logic of the application in question.  What is the unit test *really* testing in this scenario?

Even with Twisted, which has arguably the best testing practices in all of network asychrony, the threaded async APIs break the Django test runner.
 
 However, hendrix provides diplomacy between the two, resulting in [an elegant, simple test methodology](testing-asynchrony.md).

#### The time of execution is specifically determined: as soon as the response is sent over the wire

Using deferToThread will delay logic until the thread worker is available - a moment which is variable depending on the application configuration and which may even be difficult to discern by the application author.

Conversely, callFromThread will run the callable immediately in the event loop - introducing potential state clashes and race conditions.

Tasks in the crosstown_traffic queue will always run, in the order decorated, after the response has gone out over the wire to the client, minimizing stream time and removing the mystery about the application state at the time of execution.