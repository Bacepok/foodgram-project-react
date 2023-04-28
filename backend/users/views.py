from api.serializers import CustomUserSerializer, SubscribeSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated,)
from rest_framework.response import Response

from .models import Subscribe

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователя."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="subscribe",
        url_name="subscribe",
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        """Подписка/отписка на/от автора."""
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={"user": request.user.id, "author": id}
        )
        if request.method == "POST":
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            serializer = SubscribeSerializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = get_object_or_404(Subscribe, user=request.user, author__id=id)
        follow.delete()
        return Response(
            f"{request.user} отписался от {follow.author}",
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=["GET"],
        url_path="subscriptions",
        url_name="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def show_follows(self, request):
        """Просмотр подписок."""
        user_obj = User.objects.filter(following__user=request.user)
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(user_obj, request)
        serializer = SubscribeSerializer(
            result_page, many=True, context={"current_user": request.user}
        )
        return paginator.get_paginated_response(serializer.data)
