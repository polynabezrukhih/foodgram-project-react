from django.urls import include, path
from rest_framework import routers

from api.views import (
    TagViewSet,
    IngredientViewSet,
    UserViewSet,
    RecipeViewSet,
    FavoriteViewSet,
    BasketViewSet
)


app_name = 'api'
router = routers.DefaultRouter()
router.register("tags", TagViewSet, "tags")
router.register("ingredients", IngredientViewSet, "ingredients")
router.register("recipes", RecipeViewSet, "recipes")
router.register("users", UserViewSet, "users")
router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('baskets', BasketViewSet, basename='basket')

urlpatterns = [
    path("v1/", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken"))
]
