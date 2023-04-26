from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
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
    ingredients = serializers.SerializerMethodField(
        source='ingredients_in_recipe',
        read_only=True,
        many=True
    )
    author = CustomUserSerializer()

    class Meta:
        model = Recipe
        fields = '__all__'

    def check_anonymous_help_func(self, obj, model):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self.validator(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.validator(obj, ShoppingCart)

    def get_ingredients(self, obj):
        queryset = IngredientsInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(queryset, many=True).data


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
        source='ingredients_in_recipe'
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
        ingredients = data['ingredients']
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент'
            })
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты должны быть разными'
                })
            ingredients_list.append(ingredient_id)
            amount = ingredient['amount']
            if int(amount) <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше нуля'
                })

        tags = data['tags']
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один тэг'
            })
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Тэги не должны повторяться'
                })
            tags_list.append(tag)

        cooking_time = data['cooking_time']
        if int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше нуля'
            })
        return data

    @staticmethod
    def create_link_ingredients_recipe(ingredients_obj, recipe):
        for obj in ingredients_obj:
            IngredientsInRecipe.objects.create(
                recipe=recipe,
                ingredient=obj['id'],
                amount=obj['amount']
            )

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients_obj = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_link_ingredients_recipe(ingredients_obj, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients_obj = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.ingredients.clear()
        instance.tags.set(validated_data['tags'])
        self.create_link_ingredients_recipe(ingredients_obj, instance)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeRetrieveSerializer(instance, context=context).data


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
