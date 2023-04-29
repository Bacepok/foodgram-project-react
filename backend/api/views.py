from io import StringIO

from django.shortcuts import get_list_or_404, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .filters import RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (TagSerializer,
                          IngredientSerializer,
                          RecipeRetrieveSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeMinifiedSerializer)
from .utils import PlainTextRenderer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = [SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeRetrieveSerializer
        return RecipeCreateUpdateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)


class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecipeMinifiedSerializer
    http_method_names = ['post', 'delete']
    model = Favorite

    def get_queryset(self):
        return get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))

    def create(self, request, *args, **kwargs):
        user = self.request.user
        recipe = self.get_queryset()
        if not self.model.objects.filter(user=user, recipe=recipe).exists():
            self.model.objects.create(user=user, recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        recipe = self.get_queryset()
        instance = get_object_or_404(self.model, user=user, recipe=recipe)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(FavoriteViewSet):
    model = ShoppingCart


@api_view(['GET'])
@renderer_classes([PlainTextRenderer])
def download_shopping_cart(request):
    user = request.user
    cart = get_list_or_404(
        ShoppingCart.objects.select_related('recipe').prefetch_related(
            'ingredients'
        ),
        user=user
    )
    ingredients = []
    for i in cart:
        ingredients.extend(
            i.recipe.ingredients.all()
        )
    ingredients_dict = {}
    for i in ingredients:
        if i.ingredient_id not in ingredients_dict:
            ingredients_dict[i.ingredient_id] = 0
        ingredients_dict[i.ingredient_id] += i.amount
    data = StringIO()
    for i in ingredients_dict:
        ingredient = Ingredient.objects.get(id=i)
        text = f'{ingredient.name} ({ingredient.measurement_unit}) —'
        text += f' {ingredients_dict[i]} \n'
        data.write(text)
    data.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="list.txt"',
    }
    return Response(data, status=status.HTTP_200_OK, headers=headers)
