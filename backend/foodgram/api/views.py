from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponse
from api.permissions import IsAuthorOrReadOnlyPermission
from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated

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
    IngredientInRecipe
)
from users.models import User, Follow
from api.paginator import Pagntr


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagntr

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
                follower__user=request.user
            )
        )
        serializer = FollowSerializer(
            result, many=True
        )
        return self.get_paginated_response(serializer.data)


# @api_view(['GET'])
class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# @api_view(['GET'])
class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


# @api_view(['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnlyPermission, ]

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
            'recipes': pk,
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

    def download_shopping_cart(self, request):
        text = 'Список покупок:'
        user = request.user
        filename = f'{user.username}_shopping_list.txt'
        ingredients = IngredientInRecipe.objects.filter(
            recipe__basket_list__user=user
        ).values(
            'ingredient__name', 'ingredient__measure',
        ).annotate(amount=sum('amount'))
        for ingredients in ingredients:
            name, measurement_unit, amount = ingredients
            text += f'{name}: {amount} {measurement_unit}\n'
        response = HttpResponse(
            text, content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
