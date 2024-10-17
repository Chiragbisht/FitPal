from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# Create your models here.
from django.contrib.auth.models import User

# In your models.py if you are using a custom user model
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    # Other fields...


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'

    class Meta:
        ordering = ['timestamp']