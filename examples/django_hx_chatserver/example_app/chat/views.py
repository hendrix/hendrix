from django.shortcuts import render

from .models import ChatMessage


# Create your views here.


def home(request, chat_channel_name=None):
    """
        if we have a chat_channel_name kwarg,
        have the response include that channel name
        so the javascript knows to subscribe to that
        channel...
    """

    if not chat_channel_name:
        chat_channel_name = 'homepage'

    context = {
        'address': chat_channel_name,
        'history': [],
    }

    if ChatMessage.objects.filter(channel=chat_channel_name).exists():
        context['history'] = ChatMessage.objects.filter(
            channel=chat_channel_name)


    # TODO add https 
    websocket_prefix = "ws"
    websocket_port = 9000

    context['websocket_prefix'] = websocket_prefix
    context['websocket_port'] = websocket_port

    return render(request, 'chat.html', context)
