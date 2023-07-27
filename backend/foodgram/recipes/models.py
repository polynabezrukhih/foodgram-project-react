from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_lenght=settings.MAX_LENGTH,
        unique=True
    )
    color = models.CharField(
        validators=[RegexValidator(regex='#(?:[A-Fa-f0-9]{3}){1, 2}$')],
        unique=True
    )
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField( max_lenght=settings.MAX_LENGTH,)
    measure = models.CharField( max_lenght=settings.MAX_LENGTH,)
    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты' #добавить остальным классам
    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_lenght=settings.MAX_LENGTH,)
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
    time = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.text[:settings.SHOW_RECIPE_TEXT]


class IngredientToRecipe(models.Model):
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
    amount = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])


class Favorite(models.Model):
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
        verbose_name = 'Избранное'


class Basket(models.Model):
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
        verbose_name = 'Корзина покупок'
