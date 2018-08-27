import requests

counter = 0

for counter in range(5000):
    r = requests.get('http://localhost:8000/fib/%s' % counter)
    print
    "%s - %s" % (counter, r)
