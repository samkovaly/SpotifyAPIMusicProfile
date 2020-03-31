from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.contrib.auth.models import User



class UserProfile(models.Model):
    music_profile_JSON = models.TextField(blank=True)
    refresh_token = models.CharField(max_length=256)
    last_refreshed = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    initialized = models.BooleanField(default=False)


    def __str__(self):
        return self.user.username + "'s profile"



from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=User)
def build_profile_on_user_creation(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile(user=instance, initialized=False)
        profile.save()

'''
class MyAccountManager(BaseUserManager):
    def create_user(self, username, password=None):
        print("loloooll")
        if not username:
            raise ValueError("User must have a username")

        user = self.model(
            username = username
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        
        user = self.create_user(
            username = username,
            password = password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    username        = models.CharField(max_length=30, unique=True)
    password        = models.CharField(max_length=256, verbose_name='password')
    music_profile   = models.TextField(blank=True)

    date_joined     = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login      = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_active       = models.BooleanField(default=True)
    is_superuser    = models.BooleanField(default=False)

    is_staff        = models.BooleanField(default=False)
    is_admin        = models.BooleanField(default=False)

    # what they login with
    USERNAME_FIELD = 'username'
    #REQUIRED_FIELDS = ['username']

    objects = MyAccountManager()

    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True



from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist



class AccountBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        print('hehe')
        username = kwargs['username']
        password = kwargs['password']
        print(username, password)
        try:
            print("a")
            account = Account.objects.get(username=username)
            print(account)
            print('pass', account.password)
            if account.check_password(password) is True:
                print("1")
                return account
            print('2')
        except ObjectDoesNotExist:
            pass
'''