import time

from django.shortcuts import render

from hendrix.experience import crosstown_traffic, hey_joe


def my_noodles(request):
    llama = "Another noodle"

    @crosstown_traffic()
    def my_long_thing():
        for i in range(5):
            print("another noodle on the python console")
            time.sleep(1)
            hey_joe.send(llama, topic="noodly_messages")
        hey_joe.broadcast("Notice to everybody: finished noodling.")

    if request.META.get("wsgi.url_scheme") == "https":
        websocket_prefix = "wss"
        websocket_port = 9443
    else:
        websocket_prefix = "ws"
        websocket_port = 9000

    return render(request, 'noodles.html', {"websocket_prefix": websocket_prefix,
                                            "websocket_port": websocket_port})
