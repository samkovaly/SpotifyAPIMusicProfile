from django.contrib import admin

from django.urls import path
from django.conf.urls import include

from .spotify import get_spotify_music_profile

from musicProfile.views import SpotifyAppCredentials, ConcertsAPICredentials
from musicProfile.views import UserRegister, UserLogin
from musicProfile.views import UserDetail, UserProfileDetail


urlpatterns = [
    path('spotify-app-credentials/', SpotifyAppCredentials.as_view()),
    path('concerts-APIs-credentials/', ConcertsAPICredentials.as_view()),
    path('register/', UserRegister.as_view()),
    path('login/', UserLogin.as_view()),
    path('users/<str:username>', UserDetail.as_view()),
    path('users/music_profile/<str:username>', UserProfileDetail.as_view()),
]



'''
URL patterns
    auth/
        get user token
    api/users/<str:username>/
        get user by username, returns user music_profile as part of user
            must pass auth token
    api/users/<str:username>/set_music_profile/
        set users music profile
            must pass auth token
'''