from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# Create your models here.
from django.contrib.auth.models import User

# In your models.py if you are using a custom user model
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    # Other fields...