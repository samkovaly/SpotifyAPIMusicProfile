
from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from myartistsapi.views import Ping

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('musicProfile.urls')),
    path('ping', Ping.as_view()),
]