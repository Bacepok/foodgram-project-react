from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
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


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(
            queryset=Recipe.objects.all(),
            message='Рецепт с таким именем уже существует')],
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientsListingSerializer(
        many=True,
        source='ingredients'
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Время приготовления должно быть 1 или более.'
            ),
        )
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'Ингредиент был выбран несколько раз'
            )
        return data

    def to_representation(self, instance):
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        representation = super().to_representation(instance)
        representation['ingredients'] = RecipeRetrieveSerializer(
            IngredientsInRecipe.objects.filter(recipe=instance), many=True
        ).data
        representation['tags'] = TagSerializer(
            instance.tags, many=True
        ).data
        return representation

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        bulk_create_data = [
            IngredientsInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount'])
            for ingredient_data in ingredients_data
        ]
        IngredientsInRecipe.objects.bulk_create(bulk_create_data)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients' in self.validated_data:
            ingredients_data = validated_data.pop('ingredients')
            with transaction.atomic():
                amount_set = IngredientsInRecipe.objects.filter(
                    recipe__id=instance.id)
                amount_set.delete()
                bulk_create_data = (
                    IngredientsInRecipe(
                        recipe=instance,
                        ingredient=ingredient_data['ingredient'],
                        amount=ingredient_data['amount'])
                    for ingredient_data in ingredients_data
                )
                IngredientsInRecipe.objects.bulk_create(bulk_create_data)
        return super().update(instance, validated_data)


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
