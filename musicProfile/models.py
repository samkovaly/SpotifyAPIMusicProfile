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



class InterestedConcert(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    concert_seatgeek_id = models.CharField(max_length=256)



from django.dispatch import receiver
from django.db.models.signals import post_save


# after saving a new User model, a UserProfile is created automatially.
# for every User, there is one UserProfile.
@receiver(post_save, sender=User)
def build_profile_on_user_creation(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile(user=instance, initialized=False)
        profile.save()