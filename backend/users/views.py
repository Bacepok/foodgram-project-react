from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from api.pagination import PageLimitPagination
from users.serializers import SubscriptionSerializer
from rest_framework.response import Response

User = get_user_model()


def create_or_delete_record(request, record, serializer_data, params):
    if request.method == 'POST':

        if record.exists():
            raise exceptions.ValidationError('records already exists.')

        record.create(user=request.user, **params)
        return Response(serializer_data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        if not record.exists():
            raise exceptions.ValidationError('records does not exists.')
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CustomUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    @action(
        detail=False,
        methods=('get',),
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        authors = self.request.user.follower.values('author__id')
        queryset = User.objects.filter(pk__in=authors)
        serializer = self.get_serializer(
            self.paginate_queryset(queryset), many=True
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        serializer_class=SubscriptionSerializer,
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        in_follow = user.follower.filter(author=author)
        if request.method == 'POST' and user == author:
            raise exceptions.ValidationError('you can`t subscribe to yourself')

        return create_or_delete_record(
            request=request,
            record=in_follow,
            serializer_data=self.get_serializer(author).data,
            params={'author': author},
        )
