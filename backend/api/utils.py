from django_filters.rest_framework import (AllValuesMultipleFilter, FilterSet,
                                           NumberFilter)
from recipes.models import Recipe
from rest_framework.renderers import BaseRenderer


class RecipeFilter(FilterSet):
    is_favorited = NumberFilter(
        method='get_is_favorited',
    )
    tags = AllValuesMultipleFilter(
        field_name='tags__slug',
        label='tags',
    )
    is_in_shopping_cart = NumberFilter(
        method='get_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            return queryset.filter(is_favorited__user=user)
        if value == 0:
            return queryset.exclude(is_favorited__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            return queryset.filter(is_in_shopping_cart__user=user)
        if value == 0:
            return queryset.exclude(is_in_shopping_cart__user=user)
        return queryset


class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return data
