### Temporary Documentation for crosstown_traffic

crosstown_traffic is a decorator that will defer logic inside a view until a later time and run it on a different thread or threads.

For example, let's say we are building a REST endpoint that causes 100 phone calls to be placed via the twilio API.

We don't want to wait, obivously, until 100 API calls are made in order to send our response back to the client.

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


      return HttpResponse('this is synchronous')

      # And only now that we've got the response out over the wire will place_100_phone_calls happen.
```
