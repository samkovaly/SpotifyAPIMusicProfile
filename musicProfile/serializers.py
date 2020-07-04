from rest_framework import serializers
from musicProfile.models import UserProfile, InterestedConcert
#from musicProfile.models import Account
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class InterestedConcertSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestedConcert
        fields = ['concert_seatgeek_id', 'user']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['music_profile_JSON', 'refresh_token', 'last_refreshed', 'user']
        extra_kwargs = {'refresh_token': {'write_only': True, 'required': True}}
        

class UserSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer(required = False)
    Interestedconcert = InterestedConcertSerializer(required = False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'userprofile', 'interestedconcert')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user


'''
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['username', 'password', 'music_profile', 'date_joined']
        #extra_kwargs = {'password': {'write_only': True, 'required': True}}

        def create(self, validated_data):
            print('looollolol')
            user = Account.objects.create(
                email=validated_data['email'],
                username=validated_data['username'],
                password = make_password(validated_data['password'])
            )
            print('hey there, ', user)
            return user
'''