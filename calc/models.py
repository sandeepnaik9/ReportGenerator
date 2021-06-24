from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
class Profile(models.Model):
    user1 = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    job_title  = models.CharField(max_length=100,blank=True,null=True)
    phone_number = models.CharField(max_length=10,blank=True,null=True)
    address = models.TextField(blank=True,null=True)
    def __str__(self):
        return self.user1.username

class LoggedInUser(models.Model):
    user = models.OneToOneField(User, related_name='logged_in_user',on_delete=models.CASCADE)
    session_key = models.CharField(max_length=32,blank=True,null=True)

    def __str__(self):
        return self.user.username


