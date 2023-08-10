from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=settings.MAX_LENGTH,
        unique=True
    )
    color = models.CharField(
        validators=[RegexValidator(
            regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        )],
        unique=True,
        max_length=settings.COLOR_MAX_LENGTH,
    )
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=settings.MAX_LENGTH)
    measurement_unit = models.CharField(max_length=settings.MAX_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=settings.MAX_LENGTH, )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/'
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.text[:settings.SHOW_RECIPE_TEXT]


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_list'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_list'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipes', 'user',),
                name='unique_favorites_for_recipes'
            ),
        ]
        verbose_name = 'Избранное'


class Basket(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='basket_list'
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='basket_list'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipes', 'user',),
                name='unique_baskets_for_recipes'
            ),
        ]
        verbose_name = 'Корзина покупок'
