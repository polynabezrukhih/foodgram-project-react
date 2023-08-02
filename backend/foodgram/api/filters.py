from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug'
    )
    is_favorite = filters.NumberFilter(method='get_is_in_favorite')
    is_in_shopping_cart = filters.NumberFilter(method='get_is_in_basket')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorite', 'is_in_shopping_cart')

    def get_is_in_favorite(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_list__user=user)
        return queryset

    def get_is_in_basket(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(basket_list__user=user)
        return queryset
