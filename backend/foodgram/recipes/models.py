from django.conf import settings
from django.db import models
from users.models import User


class Tag(models):
    name = models.CharField(max_length=settings.MAX_LENGTH, unique=True)
    color = models.CharField(max_length=settings.COLOR_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True) #валидатор для допустимых символов(буквы,_,цифры) RegexValidator

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name


class Ingredient(models):
    name = models.CharField(max_length=settings.MAX_LENGTH)
    measure = models.CharField(max_length=settings.MAX_LENGTH)
    def __str__(self):
        return self.name


class Recipe(models):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=settings.MAX_LENGTH)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/'
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientToRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes'
    )
    time = models.PositiveSmallIntegerField() #применить валидаторы

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:settings.SHOW_RECIPE_TEXT]


class IngredientToRecipe(models):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    amount = models.PositiveSmallIntegerField() #валидатор


class Unit(models.Model):
    pass

class Favorite(models):
    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = 'favorite_list'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete = models.CASCADE,
        related_name = 'favorite_list'
    )

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user',),
                name='unique_favorites_for_recipes'
            ),
        ]


class Basket(models):
    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        related_name = 'basket_list'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete = models.CASCADE,
        related_name = 'basket_list'
    )

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user',),
                name='unique_baskets_for_recipes'
            ),
        ]
