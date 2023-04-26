from collections import OrderedDict

from django.db import transaction
from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import exceptions, serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        result = False
        user = self.context['request'].user
        if user.is_authenticated:
            result = Follow.objects.filter(user=user, following=obj).exists()
        return result


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = UserCreateSerializer.Meta.fields + (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class RecipeRetrieveSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredients_in_recipe',
        many=True
    )
    author = CustomUserSerializer()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validator(self, obj, model):
        result = False
        user = self.context['request'].user
        if user.is_authenticated:
            result = model.objects.filter(user=user, recipe=obj).exists()
        return result

    def get_is_favorited(self, obj):
        return self.validator(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.validator(obj, ShoppingCart)


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientsListingSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1, max_value=1000)

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for displaying recipes."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsListingSerializer(
        many=True, source='ingredients_in_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_favorited(request.user)

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_in_shopping_cart(request.user)


class RecipeCreateUpdateSerializer(RecipeSerializer):
    """Serializer for creating and updating recipes."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = IngredientsListingSerializer(
        source='ingredients_in_recipe', many=True)

    def validate(self, attrs):
        if len(attrs['tags']) > len(set(attrs['tags'])):
            raise serializers.ValidationError(
                'Unable to add the same tag multiple times.'
            )

        ingredients = [
            item['ingredient'] for item in attrs['ingredients_in_recipe']]
        if len(ingredients) > len(set(ingredients)):
            raise serializers.ValidationError(
                'Unable to add the same ingredient multiple times.'
            )

        return attrs

    @transaction.atomic
    def set_recipe_ingredients(self, recipe, ingredients):
        recipe_ingredients = [
            IngredientsInRecipe(
                recipe=recipe,
                ingredient=current_ingredient['ingredient'],
                amount=current_ingredient['amount'],
            )
            for current_ingredient in ingredients
        ]
        IngredientsInRecipe.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.set_recipe_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        instance.ingredients.clear()
        instance.tags.clear()
        super().update(instance, validated_data)
        instance.tags.set(tags)
        self.set_recipe_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        tag_id_list, tag_list = repr['tags'], []
        for tag_id in tag_id_list:
            tag = get_object_or_404(Tag, id=tag_id)
            serialized_tag = OrderedDict(TagSerializer(tag).data)
            tag_list.append(serialized_tag)
        repr['tags'] = tag_list
        return repr


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        source='following.email',
        required=False
    )
    id = serializers.IntegerField(
        source='following.id',
        required=False
    )
    username = serializers.CharField(
        source='following.username',
        required=False
    )
    first_name = serializers.CharField(
        source='following.first_name',
        required=False
    )
    last_name = serializers.CharField(
        source='following.last_name',
        required=False
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeMinifiedSerializer(
        source='following.recipes',
        many=True,
        required=False
    )
    recipes_count = serializers.IntegerField(
        source='following.recipes.count',
        required=False
    )

    class Meta:
        model = Follow
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            following_id=self.context['request'].user.id,
            user_id=obj.following_id
        ).exists()
