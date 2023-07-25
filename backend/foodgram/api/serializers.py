
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserSerializer, UserCreateSerializer, Serializer
import django.contrib.auth.password_validation as validators
from rest_framework.relations import SlugRelatedField

from recipes.models import Recipe, Tag, Ingredient, Basket, Favorite
from users.models import User

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password',)

        def validate_password(self, password):
            validators.validate_password(password)
            return password


class PasswordSerializer(Serializer):
    pass
    # TODO: итзучить и использовать функции из документации https://django.fun/ru/docs/django/4.1/topics/auth/passwords/

class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name') 


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)
    author = SlugRelatedField(
        read_only=True, slug_field='username'
    )
    is_in_favorite = ...
    is_in_basket = ...
    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            "name",
            "image",
            "text",
            'ingredients',
            'tags',
            "time",
            'is_in_favorite',
            "is_in_basket",
        )
        read_only_fields = (
            "is_in_favorite",
            "is_in_basket",
        )
