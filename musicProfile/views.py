from django.shortcuts import render

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

#from musicProfile.models import Account
from musicProfile.models import UserProfile
#from musicProfile.serializers import AccountSerializer
from musicProfile.serializers import UserProfileSerializer, UserSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import viewsets, status

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from django.http import HttpResponse

from django.http import Http404
from rest_framework.views import APIView

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.permissions import BasePermission

from django.contrib.auth.models import User

from rest_framework.decorators import api_view

from django.views.decorators.csrf import csrf_exempt


from rest_framework.exceptions import NotAuthenticated, NotFound, AuthenticationFailed

'''
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


    def create(self, request, *args, **kwargs):
        response = {'message': 'You cant create rating like that'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
'''


'''
@api_view(['GET', ])
def detail_profile_view(request, username):
    try:
        print("username", username)
        print(User.objects.all())

        user = User.objects.get(username=username)
        print('user', user)
        print('request', request)
        print('request.user', request.user)

        check_object_permissions(request.user, user)
        profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except ObjectDoesNotExist:
        raise Http404
'''

    # samtest:
    #   user: samtest
    #   pass: sam
    #   token: 891a281f41ada913e35199816dda356b243f2a89
    # samtest2:
    #   user: samtest2
    #   pass: sam2
    #   token: 6a410c71bbc14adabffb88d2c6ea877bdf42f21e


def get_user(request, want_username):
    if request.user.is_authenticated:
        auth_username = request.user.username
        # admin or user is accessing their own data
        if request.user.is_superuser or auth_username == want_username:
            user = User.objects.get(username=want_username)
            return user
        else:
            print('user auth fail')
            raise AuthenticationFailed('Header token authentication does not match with the user you are requesting data from')
    else:
        print('user not even authed')
        # user not not authed correctly
        raise NotAuthenticated("user has invalid authentication")


class UserDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, username, format=None):
        user = get_user(request, username)
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)


class UserProfileDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, username, format=None):
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)
        profile_serializer = UserProfileSerializer(profile)
        return Response(profile_serializer.data)


    def post(self, request, username, format=None):
        user = get_user(request, username)
        profile = UserProfile.objects.get(user=user)
        # update profile, then return
        # request.data has accesstoken / requesttoken
        profile_serializer = UserProfileSerializer(profile)

        return Response(profile_serializer.data)




class HasKeyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):

        '''
        print('has permisssoin')
        print('request', request.user)
        print("staff", request.user.is_staff)
        print("authed", request.user.is_authenticated)
        print('POST', request.POST)
        print('keys', request.POST.keys())
        '''
        
        if (request.method == 'GET'):
            if request.user and request.user.is_staff:
                return True
        # need special key from app to make a new user
        elif request.method == 'POST':
            if (request.user and request.user.is_staff) or ('app_key' in request.POST and request.POST['app_key'] == "LOOL"):
                return True
        return False


class UserPostGetAll(APIView):
    permission_classes = (HasKeyOrIsAdmin,)
    authentication_classes = (TokenAuthentication, )

    # register new user
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)  
        data = {}
        #print("serializer", serializer)
        if serializer.is_valid():
            account = serializer.save()
            data['response'] = 'successfully registered a new user'
            data['username'] = account.username
            token = Token.objects.get(user = account).key
            data['token'] = token
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # get all users (for me, the admin)
    def get(self, request, format=None):
        users = User.objects.all()
        usersSerializer = UserSerializer(users, many=True)
        return Response(usersSerializer.data, status=status.HTTP_200_OK)




'''
@api_view(['GET', ])
def detail_profile_view(request, username):
    try:
        print("username", username)
        print(User.objects.all())

        user = User.objects.get(username=username)
        print('user', user)
        #self.check_object_permissions(self.request, obj)
        profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except ObjectDoesNotExist:
        raise Http404

class HasKeyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):

        print('has permisssoin')
        print('request', request.user)
        print("staff", request.user.is_staff)
        print("authed", request.user.is_authenticated)
        print('POST', request.POST)
        print('keys', request.POST.keys())


        if (request.method == 'GET'):
            if request.user and request.user.is_staff:
                return True
        # need special key from app to make a new user
        elif request.method == 'POST':
            if (request.user and request.user.is_staff) or ('app_key' in request.POST and request.POST['app_key'] == "LOOL"):
                return True
        return False

class UserPostGetAll(APIView):
    permission_classes = (HasKeyOrIsAdmin,)
    authentication_classes = (TokenAuthentication, )

    def post(self, request, format=None):
        serializer = AccountSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            account = serializer.save()
            data['response'] = 'successfully registered a new user'
            data['username'] = account.username
            token = Token.objects.get(user = account).key
            data['token'] = token
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        accounts = Account.objects.all()
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)
'''




''''
class UserDetail(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, username):
        try:
            obj = Account.objects.get(username=username)
            self.check_object_permissions(self.request, obj)
            return obj
        except ObjectDoesNotExist: #Account.DoesNotExist:
            raise Http404

    def get(self, request, username, format=None):
        user = self.get_object(username)
        serializer = AccountSerializer(user)
        return Response(serializer.data)
'''
