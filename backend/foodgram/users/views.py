from django.shortcuts import render

from .models import UserFoodgram
class UserViewSet(viewsets.ModelViewSet):
    queryset = UserFoodgram.objects.all()
    permission_classes = (
        IsAuthenticated,
        IsAdmin
    )
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if (
            self.request.user.role != 'admin'
            or self.request.user.is_superuser
        ):
            return UserSerializer
        return AdminSerializer

    @action(
        detail=False,
        url_path='me',
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated, ],
        queryset=User.objects.all()
    )
    def me(self, request):
        user = get_object_or_404(User, id=request.user.id)
        if request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data, status=HTTP_200_OK)