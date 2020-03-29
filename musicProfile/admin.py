from django.contrib import admin

from musicProfile.models import UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

#admin.site.register(UserProfile)


class MyCustomUserInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profile'

class MyUserAdmin(BaseUserAdmin):
    inlines = (MyCustomUserInline, )

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)