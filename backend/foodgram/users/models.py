from django.contrib.auth.models import AbstractUser

from django.db import models


class UserFoodgram(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
    )
    email = models.EmailField(
        'Почта пользователя',
        unique=True,
        max_length=254,
    )
    password = models.CharField(
        'Пароль',
        max_length=254,
    )
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
