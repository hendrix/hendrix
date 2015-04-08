### Temporary Documentation for crosstown_traffic

@crosstown_traffic is a decorator that will defer logic inside a view until a specific phase in the response process and run it on a different thread or threads.

For example, let's say we are building a REST endpoint that causes 100 phone calls to be placed via the twilio API.

We don't want to wait, obviously, until 100 API calls are made in order to send our response back to the client.

However, we want to make those calls as soon as we're done with what the user needs.

Here's the pattern for doing this with crosstown_traffic:


```python
def my_django_view(request):

    # Do some django stuff, decide that we need to do some stuff after the request is over (like place 100 phone calls via the Twilio API)

        for phone_call_logic in 100_phone_calls:

            # 100 phone calls, each on their own thread, but not starting until the response has gone out over the wire

            @crosstown_traffic.follow_response()
            def place_100_phone_calls():
                phone_call_logic()

    # More django stuff, including ORM activity, which will resolve on this thread, before the crosstown_traffic begins.

      return HttpResponse('this is synchronous')

      # And only now that we've got the response out over the wire will place_100_phone_calls happen.
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

Obvioulsly the syntax is similar, and there are surely use cases for this exact deferToThread pattern.

However, the syntax of "treat this function pursuant to this decorator logic" puts the logic intention at the top, rather than the bottom, of the block.  In this sense, it is also similar to the @route decorator from Flash or the @detail_route decorator from Django-Rest-Framework.

##### It's far simpler to test in the Django test runner



# The time of execution is specifically determined - for example, as soon as the response is sent over the wire
