from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from rest_framework import status
from rest_framework.response import Response
from django.http.response import HttpResponse
from djoser.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    FollowSerializer,
    CreatRecipeSerializer,
    CustomUserSerializer,
    ReadBasketSerializer,
    ReadFavoriteSerializer
)
from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Basket
)
from users.models import User, Follow
from api.paginator import Pagntr
from api.mixins import CustomMixin
from api.permissions import (
    IsAdminOrReadOnlyPermission,
    IsAuthorOrReadOnlyPermission
)
from api.filters import IngredientFilter, RecipeFilter


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagntr
    lookup_field = 'id'

    @action(detail=True, methods=('POST', 'DELETE'))
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':

            subscriber = Follow.objects.create(
                user=user,
                author=author
            )
            serializer = FollowSerializer(
                subscriber,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscribe = get_object_or_404(
            Follow,
            user=user,
            author=author
        )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('GET',))
    def subscriptions(self, request):
        result = self.paginate_queryset(
            Follow.objects.filter(
                user=request.user
            )
        )
        serializer = FollowSerializer(
            result, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(CustomMixin):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnlyPermission,)
    pagination_class = None


class IngredientViewSet(CustomMixin):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnlyPermission,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnlyPermission, ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = Pagntr

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return CreatRecipeSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _common_post(self, request, pk, serializer_class):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.id,
            'recipes': recipe.id,
        }
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('POST',))
    def favorite(self, request, pk):
        return self._common_post(request, pk, ReadFavoriteSerializer)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        fav_list = get_object_or_404(
            Favorite,
            user=request.user,
            recipes=get_object_or_404(Recipe, id=pk)
        )
        fav_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def shopping_cart(self, request, pk):
        return self._common_post(request, pk, ReadBasketSerializer)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        bas_list = get_object_or_404(
            Basket,
            user=request.user,
            recipes__id=pk
        )
        bas_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('GET',))
    def download_shopping_cart(self, request):
        text = 'Список покупок:'
        user = request.user
        filename = f'{user.username}_shopping_list.txt'
        ingredients = IngredientInRecipe.objects.filter(
            recipe__basket_list__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount'))
        text += '\n'.join([f'{i.get("ingredient__name")}: {i.get("amount")} '
                           f'{i.get("ingredient__measurement_unit")}'
                           for i in ingredients])
        response = HttpResponse(
            text, content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
