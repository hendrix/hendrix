def application(environ, start_response):
    """Basic WSGI Application"""
    start_response('200 OK', [('Content-type', 'text/plain')])
    return ['Hello World!']
