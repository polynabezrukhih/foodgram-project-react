from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        unique=True, 
        validators=[RegexValidator(r'\w{,200}')] #убрать валидаторы :(
    )
    color = models.CharField(
        validators=[RegexValidator(regex='#(?:[A-Fa-f0-9]{3}){1, 2}$')],
        unique=True
    )
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(validators=[RegexValidator(r'\w{,200}')]) #убрать валидаторы :(
    measure = models.CharField(validators=[RegexValidator(r'\w{,200}')])
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
    name = models.CharField(validators=[RegexValidator(r'\w{,200}')])
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
