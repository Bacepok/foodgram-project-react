from api import views
from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter
from users.views import CustomUserViewSet

api_router = SimpleRouter()
api_router.register('tags', views.TagViewSet, basename='tag')
api_router.register(
    'ingredients', views.IngredientViewSet, basename='ingredient'
)
api_router.register('recipes', views.RecipeViewSet, basename='recipe')
api_router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/download_shopping_cart/',
        views.download_shopping_cart,
        name='download_shopping_cart',
    ),
    re_path(
        r'recipes/(?P<recipe_id>[\d]+)/favorite/',
        views.FavoriteViewSet.as_view({'post': 'create', 'delete': 'delete'}),
        name='favorite_create_delete',
    ),
    re_path(
        r'recipes/(?P<recipe_id>[\d]+)/shopping_cart/',
        views.ShoppingCartViewSet.as_view(
            {'post': 'create', 'delete': 'delete'}
        ),
        name='shopping_cart_create_delete',
    ),
    path(
        '',
        include(api_router.urls),
    ),
]
