from django.contrib import admin

from recipes.models import (
    Tag,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Basket,
    Favorite
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeInIngredientAdmin(admin.TabularInline):
    model = IngredientInRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_calc')
    list_filter = ('name', 'author__username', 'tags__name')
    search_fields = ('name', 'author__username', 'tags__name')
    readonly_fields = ('favorite_calc',)
    inlines = (RecipeInIngredientAdmin,)

    def favorite_calc(self, obj):
        return obj.favorite_list.count()

    favorite_calc.short_description = 'Добавлено в избранное'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipes')
    list_filter = ('recipes__tags',)
    search_fields = ('recipes__name', 'user__username')


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipes')
    list_filter = ('recipes__tags',)
    search_fields = ('recipes__name', 'user__username')
