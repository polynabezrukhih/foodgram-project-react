from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view

from api.serializers import TagSerializer, IngredientSerializer, RecipeSerializer
from recipes.models import Recipe, Tag, Ingredient, Basket, Favorite
from users.models import User


class UserViewSet(ModelViewSet):
    pass

@api_view(['GET'])
class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

@api_view(['GET'])
class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

@api_view(['GET','POST','DELETE'])
class RecipeViewSet(ReadOnlyModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied('Изменение чужого контента запрещено!')
        super().perform_update(serializer)

    def perform_destroy(self, serializer):
        if serializer.author != self.request.user:
            raise PermissionDenied('Изменение чужого контента запрещено!')
        super().perform_destroy(serializer)
