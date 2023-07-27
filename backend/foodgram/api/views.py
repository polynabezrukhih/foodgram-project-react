from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponse
from .permissions import IsAuthorOrReadOnlyPermission

from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ReadFavoriteSerializer,
    ReadBasketSerializer,
    FollowSerializer,
    CreatRecipeSerializer
)
from recipes.models import (
    Recipe, 
    Tag, 
    Ingredient, 
    Basket, 
    Favorite, 
    IngredientToRecipe
)
from users.models import User, Follow


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = FollowSerializer

    def subscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        subscribe = Follow.objects.create(
            following=user,
            author=author
        )
        serializer = FollowSerializer(
            subscribe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        subscribe = get_object_or_404(
            Follow, following=user, author=author
        )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def subscriptions(self, request):
        result = self.paginate_queryset(
            User.objects.filter(
                follower__user=self.request.user
            )
        )
        serializer = FollowSerializer(
            result, many=True
        )
        return self.get_paginated_response(serializer.data)


@api_view(['GET'])
class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


@api_view(['GET'])
class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


@api_view(['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnlyPermission,]

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return CreatRecipeSerializer
        return ReadRecipeSerializer

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

    def post(self, request, serializer, pk):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = serializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, model, pk):
        list = get_object_or_404(
            model,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        )
        list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def favorite(self, request, pk=None):
        return self.post(request, ReadFavoriteSerializer, pk)

    def delete_from_favorite(self, request, pk=None):
        return self.delete(request, Favorite, pk)

    def basket(self, request, pk=None):
        return self.post(request, ReadBasketSerializer, pk)

    def delete_from_basket(self, request, pk=None):
        return self.delete(request, Basket, pk)
    
    def download_basket(self, request):
        text = 'Список покупок:'
        user = self.request.user
        filename = f"{user.username}_shopping_list.txt"
        ingredients = IngredientToRecipe.objects.filter(
            recipe__basket_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measure',
        ).annotate(amount=sum('amount'))
        for ingredients in ingredients:
            name, measurement_unit, amount = ingredients
            text += f'{name}: {amount} {measurement_unit}\n'
        response = HttpResponse(
            text, content_type="text.txt"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response 


# class FavoriteViewSet(ModelViewSet):
#     queryset = Recipe.objects.all()
#     serializer_class = ReadBasketSerializer


# class BasketViewSet(ModelViewSet):
#     queryset = Recipe.objects.all()
#     serializer_class = ReadFavoriteSerializer

