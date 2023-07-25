from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer, Serializer
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.relations import SlugRelatedField

from recipes.models import Recipe, Tag, Ingredient, Basket, Favorite
from users.models import User

import django.contrib.auth.password_validation as validators

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
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed') 


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
                message=('Такой ингредиент уже есть.')
            )
        ]


class RecipeSerializer(ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)
    author = SlugRelatedField(
        read_only=True, slug_field='username'
    )

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
    def is_in_favorite(self, obj):
        if self.context['request'].user.is_authenticated:
            user = get_object_or_404(
                User, username=self.context['request'].user)
            return ...
        return False

    def is_in_basket(self, obj):
        if self.context['request'].user.is_authenticated:
            user = get_object_or_404(
                User, username=self.context['request'].user)
            return ...
        return False
