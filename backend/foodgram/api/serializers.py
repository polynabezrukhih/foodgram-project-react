from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.serializers import (
    ModelSerializer,
    ValidationError,
    CurrentUserDefault,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
    IntegerField
)
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.relations import SlugRelatedField
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
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password',)

    # def create(self, validated_data):
    #     user = User(
    #         email=validated_data['email'],
    #         username=validated_data['username'],
    #         first_name=validated_data['first_name'],
    #         last_name=validated_data['last_name'],
    #     )
    #     user.set_password(validated_data['password'])
    #     user.save()
    #     return user


class FollowSerializer(ModelSerializer):
    user = SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=CurrentUserDefault(),
    )
    following = SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')
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

    def is_subscribed(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user,
                author=obj.id
            ).exists()
        return False

    def recipes(self, obj):
        request = Recipe.objects.filter(author=obj.id)
        serializer = RecipeForListSerializer(request, many=True)
        return serializer.data

    def recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.id).count()


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user,
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


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredients.id')
    name = ReadOnlyField(source='ingredients.name')
    measurement_unit = ReadOnlyField(source='ingredients.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = '__all__'


class RecipeForListSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'image',
            'tags',
            'cooking_time',
        )


class ReadRecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='ingredient')
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
        Ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(Ingredients, many=True).data


class CreatRecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all)
    ingredients = IngredientInRecipeSerializer(many=True)
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

    def velidate(self, data):
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
                ingredients=get_object_or_404(Ingredient, id=ingredient['id']),
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
        self.create_ingredients(ingredients, instance)
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class ReadBasketSerializer(ModelSerializer):
    class Meta:
        model = Basket
        fields = ('user', 'recipes')

    def validate(self, attrs):
        user = attrs['user']
        if user.favorite_list.filter(recipes=attrs['recipes']).exists():
            raise ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.instance.tags.set(instance).clear()
        recipes = validated_data.pop('recipes')
        instance.recipes.set(recipes)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class ReadFavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipes')

    def validate(self, attrs):
        user = attrs['user']
        if user.basket_list.filter(recipes=attrs['recipes']).exists():
            raise ValidationError(
                'Рецепт уже добавлен в корзину.'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.instance.tags.set(instance).clear()
        recipes = validated_data.pop('recipes')
        instance.recipes.set(recipes)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data
