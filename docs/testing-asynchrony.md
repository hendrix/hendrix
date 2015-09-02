## Testing crosstown_traffic in a web view

Consider the following Django / Pyramid / Flask view:

```python
def view_that_sends_email(request):

    validated = validate_stuff_from_request(request)
    
    @crosstown_traffic()
    def send_email_later():
        long_email_api_call()
    
    return Response('template.html', {'validated': validated})
```

You can totally test this view in your normal way - pass it a valid request object and inspect the response.

Note that the crosstown_traffic in this case will have been run immediately - before the view even yields.  (This is the default behavior for crosstown_traffic that is run outside a stream (ie, with no response bound to the current thread)).

However, if want to simulate the situation of having a queue of crosstown_tasks to run following a view, hendrix provides two facilities for doing so.

### Using the AsyncTestMixin

The first is a test mixin that lives at `hendrix.utils.test_utils.AsyncTestMixin`.

```python
class TestEmailSending(AsyncTestMixin, TestCase):

    def test_that_something_is_added_to_crosstown_traffic(self):
        '''
        Simple test to show that 1 item is added to crosstown_traffic
        during the view_that_sends_email()
        '''
        r = Request()
        view_that_sends_email(r)
        
        self.assertNumCrosstownTasks(1)
```

If all you need to know is the number of tasks that will be run after the Response is complete, assertNumCrosstownTasks is the easiest way to achieve this.  

Sometimes you also want to actually inspect the callable(s) in the queue, though:

```python
class TestEmailSending(AsyncTestMixin, TestCase):

    def test_that_email_is_actually_sent(self):
        '''
        Shows that the callable that runs after the Response
        actually sends email.
        '''
    
        r = Request()
        view_that_sends_email(r)
        
        # The view is done, but the emails haven't been sent.
        self.assertFalse(some_email_batch.has_been_sent)
        
        # Now we have the callable that we sent to crosstown.
        long_email_api_call = self.next_task()   
        long_email_api_call()
        
        self.assertTrue(some_email_batch.has_been_sent)
```

### Using crosstownTaskListDecoratorFactory

An even simpler, albeit less feature-rich, approach to testing crosstown_traffic is to supply your own list to which you want crosstown_traffic callables to be appended.

This test examines the same view as above:

```python
class TestEmailSending(TestCase):

    def test_that_email_sender_is_added_to_crosstown_traffic(self):
        '''
        Shows that the callable that runs after the Response
        actually sends email.
        '''
        
        from hendrix.experience import crosstown_traffic
        from hendrix.utils.test_utils import crosstownTaskListDecoratorFactory
        
        my_task_list = []
        crosstown_traffic.decorator = crosstownTaskListDecoratorFactory(my_task_list)
    
        r = Request()
        view_that_sends_email(r)
        
        # The view is done, but the emails haven't been sent.
        self.assertFalse(some_email_batch.has_been_sent)
        
        # Now we have the callable that we sent to crosstown.
        long_email_api_call = my_task_list[0]
        long_email_api_call()
        
        self.assertTrue(some_email_batch.has_been_sent)
```

