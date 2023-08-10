from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.serializers import (
    ModelSerializer,
    ValidationError,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
    IntegerField
)
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    Basket,
    Favorite,
    IngredientInRecipe
)
from users.models import User, Follow


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class FollowSerializer(ModelSerializer):
    id = ReadOnlyField(source='author.id')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('is_subscribed', 'recipes_count', 'recipes',
                  'id', 'username', 'first_name', 'last_name')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Уже подписаны',
            )
        ]

    def validate(self, data):
        user = self.context['request'].user
        follow_obj = data['following']
        if user == follow_obj:
            raise ValidationError(
                'Невозможно подписаться на самого себя'
            )
        return data

    def get_is_subscribed(self, obj):
        request = self.context.get('request').user
        if request.is_authenticated:
            return Follow.objects.filter(
                user=request,
                author=obj.id
            ).exists()
        return False

    def get_recipes(self, obj):
        recipes_limit = (
            self.context.get('request').query_params.get('recipes_limit'))
        queryset = (obj.author.recipes.all()[:int(recipes_limit)]
                    if recipes_limit
                    else obj.author.recipes.all())
        return RecipeForListSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request').user
        if request.is_authenticated:
            return Follow.objects.filter(
                user=request,
                author=obj.id
            ).exists()
        return False


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=('name', 'unit'),
                message='Такой ингредиент уже есть.'
            )
        ]


class ReadIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeForListSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'tags',
            'cooking_time',
        )


class ReadRecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='recipe_ingredients')
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = (
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'tags',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.favorite_list.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.basket_list.filter(user=request.user).exists()
        return False

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data


class CreatRecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = ReadIngredientSerializer(many=True)
    image = Base64ImageField()
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time'
        )

    def validate(self, data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        if not ingredients:
            raise ValidationError('Выберите ингердиенты.')
        if not tags:
            raise ValidationError('Выберите хотя бы один тег.')

        data.update(
            {
                'tags': tags,
                'ingredients': ingredients,
                'author': self.context.get('request').user,
            }
        )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append(IngredientInRecipe(
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ))
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class ReadBasketSerializer(ModelSerializer):
    class Meta:
        model = Basket
        fields = '__all__'

    def to_representation(self, instance):
        return RecipeForListSerializer(
            instance.recipes,
            context={'request': self.context.get('request')}
        ).data


class ReadFavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

    def to_representation(self, instance):
        return RecipeForListSerializer(
            instance.recipes,
            context={'request': self.context.get('request')}
        ).data
