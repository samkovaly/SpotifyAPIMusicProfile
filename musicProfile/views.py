from rest_framework.response import Response

from rest_framework import status
from django.http import JsonResponse

from django.contrib.auth.models import User
from musicProfile.models import UserProfile
from musicProfile.serializers import UserProfileSerializer, UserSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission

from rest_framework.views import APIView

from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed

from musicProfile.spotify import get_spotify_music_profile

import sys
sys.path.append("..")
from local_secrets import spotify_app_credentials, concerts_events_API_credentials


    # samtest:
    #   user: samtest
    #   pass: sam
    #   token: 891a281f41ada913e35199816dda356b243f2a89
    # samtest2:
    #   user: samtest2
    #   pass: sam2
    #   token: 6a410c71bbc14adabffb88d2c6ea877bdf42f21e


# requried user's own tooken or the master token
def get_user(request, want_username):
    if request.user.is_authenticated:
        auth_username = request.user.username
        # admin or user is accessing their own data
        if request.user.is_superuser or auth_username == want_username:
            user = User.objects.get(username=want_username)
            return user
        else:
            #print('user auth fail')
            raise AuthenticationFailed('Header token authentication does not match with the user you are requesting data from')
    else:
        #print('user not even authed')
        # user not not authed correctly
        raise NotAuthenticated("user has invalid authentication")


# requried user's own token or the master token
class UserDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, username, format=None):
        user = get_user(request, username)
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)



# requried user's own token or the master token
class UserProfileDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # get music profile
    def get(self, request, username, format=None):
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)
        profile_serializer = UserProfileSerializer(profile)
        return Response(profile_serializer.data)

    # refresh user music profile
    # needs master toke in header and a valid access token passed as data to work.
    def post(self, request, username, format=None):
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)

        access_token = request.POST.get("access_token")
        new_music_profile_JSON = get_spotify_music_profile(access_token)
        profile.music_profile_JSON = new_music_profile_JSON.content
        profile.save()

        profile_serializer = UserProfileSerializer(profile)
        return Response(profile_serializer.data)

'''
class HasKeyOrIsAdmin(BasePermission):
    def has_permission(self, request, view):
        if (request.method == 'GET'):
            if request.user and request.user.is_staff:
                return True
        # need special key from app to make a new user
        elif request.method == 'POST':
            if (request.user and request.user.is_staff) or ('app_key' in request.POST and request.POST['app_key'] == "LOOL"):
                return True
        return False
'''

# admin can get all users or make a new user
# requires admin's token (coming from the app)
class UserPostOrGetAll(APIView):
    permission_classes = (IsAdminUser,)
    authentication_classes = (TokenAuthentication, )

    # register new user
    def post(self, request, format=None):
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid() and 'refresh_token' in request.data:

            user = User.objects.create_user(username=request.data['username'],
                                 password=request.data['password'])
            profile = UserProfile.objects.get(user=user)
            profile.refresh_token = request.data['refresh_token']
            profile.save()

            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # get all users (for me, the admin)
    def get(self, request, format=None):
        users = User.objects.all()
        usersSerializer = UserSerializer(users, many=True)
        return Response(usersSerializer.data, status=status.HTTP_200_OK)


# requires admin's token (coming from the app)
class SpotifyAppCredentials(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAdminUser,)

    def get(self, request, format=None):
        return JsonResponse(spotify_app_credentials)
        

# requires admin's token (coming from the app)
class ConcertsAPICredentials(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAdminUser,)
    def get(self, request, format=None):
        return JsonResponse(concerts_events_API_credentials)