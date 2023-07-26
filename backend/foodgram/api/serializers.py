from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer, Serializer, SerializerMethodField
from rest_framework.serializers import ModelSerializer, ValidationError, CurrentUserDefault, PrimaryKeyRelatedField, ReadOnlyField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.relations import SlugRelatedField
from drf_extra_fields.fields import Base64ImageField


from recipes.models import Recipe, Tag, Ingredient, Basket, Favorite, IngredientToRecipe
from users.models import User, Follow

import django.contrib.auth.password_validation as validators


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password',)

    def validate_password(self, password):
        validators.validate_password(password)
        return password


class PasswordSerializer(Serializer):
    pass
    # TODO: итзучить и использовать функции из документации https://django.fun/ru/docs/django/4.1/topics/auth/passwords/


class FollowSerializer(ModelSerializer):
    user = SlugRelatedField(
        read_only=True,
        slug_field="username",
        default=CurrentUserDefault(),
    )
    following = SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ("user", "following")
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=("user", "following"),
                message="Уже подписаны",
            )
        ]
    def validate(self, data):
        user = self.context["request"].user
        follow_obj = data["following"]
        if user == follow_obj:
            raise ValidationError(
                "Невозможно подписаться на самого себя"
            )
        return data
    def is_follower(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, author=obj.id).exists()
        return False

    def recipes(self, obj):
        request = Recipe.objects.filter(author=obj.id)
        serializer = RecipeForListSerializer(request, many=True)
        return serializer.data

    def recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.id).count()


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')


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


class IngredientToRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredients.id')
    name = ReadOnlyField(source='ingredients.name')
    measure = ReadOnlyField(source='ingredients.measure')

    class Meta:
        model = IngredientToRecipe
        fields = '__all__'


class RecipeForListSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "name",
            "image",
            'tags',
            "time",
        )

class ReadRecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = SlugRelatedField(
        read_only=True, slug_field='username'
    )
    ingredients = IngredientToRecipeSerializer(many=True, source='ingredients')
    is_in_favorite = SerializerMethodField(method_name='is_in_favorite')
    is_in_basket = SerializerMethodField(method_name='is_in_basket')
    image = Base64ImageField()

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
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return obj.favorite_list.filter(user=request.user).exists()
        return False

    def is_in_basket(self, obj):
        request = self.context.get('request')
        if request is not None and request.user.is_authenticated:
            return obj.basket_list.filter(user=request.user).exists()
        return False


class CreatRecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all)

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
            "time"
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
                "tags": tags,
                "ingredients": ingredients,
                "author": self.context.get("request").user,
            }
        )
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = self.initial_data.get('tags')
        recipe = Recipe.objects.create(author=CurrentUserDefault()(self), **validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            id = ingredient.get('id')
            amount = ingredient.get('amount')
            ingredient_recipe, created = (
                IngredientToRecipe.objects.get_or_create(
                    recipe=recipe,
                    id=id,
                    defaults={'amount': amount}
                )
            )
            if not created:
                ingredient_recipe.amount = amount
                ingredient_recipe.save()
        return recipe


    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            amount = ingredient['amount']
            if IngredientToRecipe.objects.filter(
                recipe=recipe,
                ingredients=get_object_or_404(Ingredient, id=ingredient['id']),
            ).exists()
            IngredientToRecipe.objects.update_or_create(
                recipe=recipe,
                ingredients=get_object_or_404(Ingredient, id=ingredient['id']),
                defaults={"amount": amount},
            )

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        IngredientToRecipe.objects.filter(recipe=recipe).delete()
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)
    
    def to_representation(self, recipe):
        data = ReadRecipeSerializer(
            recipe, context={"request": self.context.get("request")}
        ).data
        return data


class ReadBasketSerializer(ModelSerializer):
    class Meta:
        model = Basket
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = attrs['user']
        if user.favorite_list.filter(recipe=attrs['recipe']).exists():
            raise ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return attrs
    def update(self, basket_list, validated_data):
        basket_list = validated_data.pop('recipes')
        return super().update(basket_list, validated_data)


class ReadFavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = attrs['user']
        if user.basket_list.filter(recipe=attrs['recipe']).exists():
            raise ValidationError(
                'Рецепт уже добавлен в корзину.'
            )
        return attrs

    def update(self, instance, validated_data):
        favorite_list = validated_data.pop('recipes')
        return super().update(favorite_list, validated_data)

