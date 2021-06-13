from django.contrib import admin

from calc.models import Profile,LoggedInUser
# Register your models here.


admin.site.register(Profile)
admin.site.register(LoggedInUser)