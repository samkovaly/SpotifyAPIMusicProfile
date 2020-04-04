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
from local_secrets import SECRET_APP_KEY

from musicProfile.spotify_auth_functionality import fetch_user_id
from django.contrib.auth import authenticate


PASSWORD_LENGTH = 20





class HasAppKey(BasePermission):
    def has_permission(self, request, view):
        if "HTTP_AUTHORIZATION" in request.META:
            if request.META['HTTP_AUTHORIZATION'] == "Token " + SECRET_APP_KEY:
                return True
        return False

# requires admin's token (coming from the app)
class SpotifyAppCredentials(APIView):
    permission_classes = (HasAppKey,)
    def get(self, request, format=None):
        return JsonResponse(spotify_app_credentials)

# requires admin's token (coming from the app)
class ConcertsAPICredentials(APIView):
    permission_classes = (HasAppKey,)
    def get(self, request, format=None):
        return JsonResponse(concerts_events_API_credentials)






def get_password_from_refresh_token(refresh_token):
    return refresh_token[0:PASSWORD_LENGTH]

def save_refresh_token_to_user(user, refresh_token):
    profile = UserProfile.objects.get(user=user)
    profile.refresh_token = refresh_token
    profile.save()

# admin can get all users or make a new user
# requires admin's token (coming from the app)
class UserRegister(APIView):
    permission_classes = (AllowAny,)

    # register new user
    # needs username, password, refresh_token and access_token
    # if user already exists, must verify access_token is correct, 
    #   then update the refresh_token and update the password
    def post(self, request, format=None):
        #print('POST api/users, data:', request.data)

        username = request.data.get("username")
        access_token = request.data.get("access_token")
        refresh_token = request.data.get("refresh_token")

        '''
        print('register')
        if username:
            print(username)
        if access_token:
            print(access_token[0:10])
        if refresh_token:
            print(refresh_token[0:10])
        '''

        # validate fields
        if username is None or access_token is None or refresh_token is None:
            return Response('Please provide: username, valid access_token and valid refresh_token',
                            status=status.HTTP_400_BAD_REQUEST)

        if fetch_user_id(access_token) != username:
            return Response("spotify access_token failed to match fetched username", status=status.HTTP_403_FORBIDDEN)

        password = get_password_from_refresh_token(refresh_token)
        
        # returning user, must update refresh_token and password, but keep musicprofile JSON
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username = username)
            save_refresh_token_to_user(user, refresh_token)
            user.set_password(password)
            user.save()
            return Response("user already exists.. updated the refresh token", status=status.HTTP_201_CREATED)

        else:
            user = User.objects.create_user(username=username, password=password)
            save_refresh_token_to_user(user, refresh_token)
            return Response("User created successfully", status=status.HTTP_201_CREATED)

class UserLogin(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get("username")
        refresh_token = request.data.get("refresh_token")

        if username is None or refresh_token is None:
            return Response('Please provide both username and refresh_token', status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=get_password_from_refresh_token(refresh_token))
        if not user:
            return Response('Invalid Credentials', status=status.HTTP_404_NOT_FOUND)
        
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)



# requried user's own token
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
        print('\ngetting music profile...')
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)
        profile_serializer = UserProfileSerializer(profile)
        print('returning:', profile_serializer.data['music_profile_JSON'][0:100], '\n')
        return Response(profile_serializer.data)

    # refresh user music profile
    # needs master toke in header and a valid access token passed as data to work.
    def post(self, request, username, format=None):
        print('\nanalyze spotify...')
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)

        access_token = request.data.get('access_token')
        if not access_token:
            return Response('Please provide a valid access token', status=status.HTTP_400_BAD_REQUEST)
        new_music_profile_JSON = get_spotify_music_profile(access_token)  

        print('\n')

        profile.music_profile_JSON = new_music_profile_JSON
        profile.save()

        profile_serializer = UserProfileSerializer(profile)
        return Response(profile_serializer.data)