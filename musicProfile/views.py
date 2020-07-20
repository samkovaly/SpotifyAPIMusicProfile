from rest_framework.response import Response

from rest_framework import status
from django.http import JsonResponse
import json

from django.contrib.auth.models import User
from musicProfile.models import UserProfile, InterestedConcert
from musicProfile.serializers import UserProfileSerializer, UserSerializer, InterestedConcertSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission

from rest_framework.views import APIView

from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed

from musicProfile.spotify import get_spotify_music_profile

import sys
sys.path.append("..")

from myartistsapi.settings import spotify_app_credentials, API_credentials
from myartistsapi.settings import SECRET_APP_KEY

from musicProfile.spotify_auth_functionality import fetch_user_id
from django.contrib.auth import authenticate

from django.shortcuts import get_object_or_404

PASSWORD_LENGTH = 20


# customer permission function for a simple auth token
class HasAppKey(BasePermission):
    def has_permission(self, request, view):
        if "HTTP_AUTHORIZATION" in request.META:
            if request.META['HTTP_AUTHORIZATION'] == "Token " + SECRET_APP_KEY:
                return True
        return False

# requires the secret app token
class SpotifyAppCredentials(APIView):
    permission_classes = (HasAppKey,)
    def get(self, request, format=None):
        return JsonResponse(spotify_app_credentials)

# requires the secret app token
class APICredentials(APIView):
    permission_classes = (HasAppKey,)
    def get(self, request, format=None):
        return JsonResponse(API_credentials)

# helper function to make status resposes
def makeStatusResp(msg, status):
    return {
        'message': msg,
        'status': status,
    }

# truncate a long refresh token into an automatic password for the user
def get_password_from_refresh_token(refresh_token):
    return refresh_token[0:PASSWORD_LENGTH]

# update the user's refresh token
def save_refresh_token_to_user(user, refresh_token):
    profile = UserProfile.objects.get(user=user)
    profile.refresh_token = refresh_token
    profile.save()

# Anyone can make a new user provided they have:
#   spotify username
#   spotify access token that has recently been aquired
#   spotify refresh token that works
#   and all these must match to the same spotify account
class UserRegister(APIView):
    permission_classes = (AllowAny,)

    # register new user
    # needs username, password, refresh_token and access_token
    # if user already exists, must verify access_token is correct, 
    #   then update the refresh_token and update the password
    def post(self, request, format=None):

        username = request.data.get("username")
        email = request.data.get("email")
        access_token = request.data.get("access_token")
        refresh_token = request.data.get("refresh_token")

        # validate fields
        if username is None or access_token is None or refresh_token is None:
            return JsonResponse(makeStatusResp('Please provide: username, valid access_token and valid refresh_token', 
            status.HTTP_400_BAD_REQUEST))


        if fetch_user_id(access_token) != username:
            return JsonResponse(makeStatusResp('spotify access_token failed to match fetched username', 
            status.HTTP_403_FORBIDDEN))

        password = get_password_from_refresh_token(refresh_token)
        
        # returning user, must update refresh_token and password, but keep musicprofile JSON
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username = username)
            save_refresh_token_to_user(user, refresh_token)
            user.set_password(password)
            if email:
                user.email = email
            user.save()
            return JsonResponse(makeStatusResp('user already exists.. updated the refresh token', status.HTTP_201_CREATED))

        else:
            if email:
                user = User.objects.create_user(username=username, password=password, email=email)
            else:
                user = User.objects.create_user(username=username, password=password)

            save_refresh_token_to_user(user, refresh_token)
            return JsonResponse(makeStatusResp('User created successfully', status.HTTP_201_CREATED))

class UserLogin(APIView):
    permission_classes = (AllowAny,)

    # standard login to get an auth token but password is generated from the refresh token provided
    def post(self, request):
        username = request.data.get("username")
        refresh_token = request.data.get("refresh_token")

        if username is None or refresh_token is None:
            return JsonResponse(makeStatusResp('Please provide both username and refresh_token', status.HTTP_400_BAD_REQUEST))

        user = authenticate(username=username, password=get_password_from_refresh_token(refresh_token))
        if not user:
            return JsonResponse(makeStatusResp('Invalid Credentials', status.HTTP_404_NOT_FOUND))
        
        token, _ = Token.objects.get_or_create(user=user)
        return JsonResponse({'token': token.key})


# does request username match the user's provided tokens
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
        return JsonResponse(user_serializer.data)

# requried user's own token or the master token
class UserProfileDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # get music profile
    def get(self, request, username, format=None):
        print('\ngetting music profile...')
        user = get_user(request, username)
        profile = get_object_or_404(UserProfile, user=user)
        #profile = UserProfile.objects.get(user=user)
        profile_serializer = UserProfileSerializer(profile)
        return JsonResponse(profile_serializer.data)

    # refresh user music profile
    # needs master toke in header and a valid access token passed as data to work.
    def post(self, request, username, format=None):
        print('\nanalyze spotify...')
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)

        access_token = request.data.get('access_token')
        if not access_token:
            return JsonResponse(makeStatusResp('Please provide a valid access token', status.HTTP_400_BAD_REQUEST))

        new_music_profile = get_spotify_music_profile(access_token)
        new_music_profile_JSON = json.dumps(new_music_profile)
        print('\n')

        if 'error' in new_music_profile:
            return JsonResponse(new_music_profile)
        else:
            profile.music_profile_JSON = new_music_profile_JSON
            profile.save()

            profile_serializer = UserProfileSerializer(profile)
            return Response(profile_serializer.data)


class InterestedConcerts(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # get user's interested concerts (list of strings)
    def get(self, request, username, format=None):
        print('\ngetting concert IDs..')
        user = get_user(request, username)
        concerts = InterestedConcert.objects.filter(user=user)
        concerts_serializer = InterestedConcertSerializer(concerts, many=True)
        
        print(concerts_serializer.data)
        return JsonResponse({"data": concerts_serializer.data})

    # post a new concert id to the interestedConcerts table
    def post(self, request, username, format=None):
        user = get_user(request, username)
        concert_seatgeek_id = request.data.get('concert_seatgeek_id')

        if InterestedConcert.objects.filter(user=user, concert_seatgeek_id=concert_seatgeek_id).exists():
            return JsonResponse(makeStatusResp('interestedConcert already exists', status.HTTP_400_BAD_REQUEST))

        concert = InterestedConcert.objects.create(user = user, concert_seatgeek_id = concert_seatgeek_id)
        concert.save()
        concerts_serializer = InterestedConcertSerializer(concert)
        
        print('returning:', concerts_serializer.data['concert_seatgeek_id'], '...\n')
        #return Response(concerts_serializer.data)
        return JsonResponse(concerts_serializer.data)


class InterestedConcertsDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # standard DEL of interested concert ID resource
    def delete(self, request, username, concert_id, format=None):
        user = get_user(request, username)
        InterestedConcert.objects.get(user=user, concert_seatgeek_id=concert_id).delete()
        #return Response('Deleted', status=status.HTTP_200_OK)
        return JsonResponse(makeStatusResp('Deleted', status.HTTP_200_OK))