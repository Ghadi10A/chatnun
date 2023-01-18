# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
# from modeltranslation.fields import TranslationField

class Prediction(models.Model):
    app_label = 'myapp'

    INSTRUMENTS = [
        ('nasdaq100', 'NASDAQ 100'),
        ('tesla', 'Tesla'),
        ('google', 'Google'),
        ('apple', 'Apple'),
        ('amazon', 'Amazon'),
        ('btc', 'Bitcoin'),
        ('gold', 'Gold'),
        ('oil', 'Oil'),
    ]

    instrument = models.CharField(max_length=50, choices=INSTRUMENTS)
    close_price = models.FloatField()
    vwap = models.FloatField()
    signal = models.CharField(max_length=50)
    accuracy = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    groups = models.ManyToManyField(Group, related_name='custom_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_permissions')  

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

# class MyModel(models.Model):
#     name = TranslationField(translated_field='name', language='en', empty_value='')
#     description = TranslationField(translated_field='description', language='en', empty_value='')

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)

     

