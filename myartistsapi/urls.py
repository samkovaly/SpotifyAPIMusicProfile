
from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from rest_framework.authtoken.views import obtain_auth_token

from .get_credentials import get_spotify_app_credentials, get_concert_API_keys

urlpatterns = [
    path('admin/', admin.site.urls),
    path('concert-APIs-credentials/', get_concert_API_keys),
    path('spotify-app-credentials/', get_spotify_app_credentials),
    path('api/', include('musicProfile.urls')),
    path('auth/', obtain_auth_token),
]