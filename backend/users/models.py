from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    USERS_ROLES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    )
    email = models.EmailField(
        'электронная почта',
        max_length=250,
        unique=True,
    )
    first_name = models.CharField(
        'имя',
        max_length=150,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=150,
    )
    role = models.CharField(
        'пользовательская роль',
        max_length=max(len(role) for role, none_ in USERS_ROLES),
        choices=USERS_ROLES,
        default=USER,
    )
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ('id',)
        indexes = [
            models.Index(fields=['role', ], name='role_idx'),
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_subscribed',
        verbose_name='Кто подписался'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_followed',
        verbose_name='На кого подписался'
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        return f'Flw: {self.user.username}->{self.following.username}'[:30]
