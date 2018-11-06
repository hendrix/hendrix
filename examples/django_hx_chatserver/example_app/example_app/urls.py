from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from chat.views import home

urlpatterns = [
               url(r'^(?P<chat_channel_name>\w+)$', home, name='home'),
               url(r'^$', home, name='home'),
               url(r'^admin/', admin.site.urls),
               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
