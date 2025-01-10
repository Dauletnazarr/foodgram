import os

from djoser.conf import settings
from djoser.views import UserViewSet
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.paginators import Pagination
from api.serializers import (
    AvatarUpdateSerializer, RecipeShortSerializer,
    SubscribedUsersSerializer, TagSerializer,
    IngredientSerializer, RecipeSerializer, UserModelSerializer
)
from api.filters import RecipeFilter
from api.permissions import AuthorOrReadOnly
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, ShoppingCart,
    Subscription, Tag, Recipe, UserModel
)


class UsersViewSet(UserViewSet):
    serializer_class = UserModelSerializer
    queryset = UserModel.objects.all()
    permission_classes = [AuthorOrReadOnly]
    pagination_class = Pagination

    def get_permissions(self):
        if self.action == 'me':
            # Используем IsAuthenticated для 'me'
            self.permission_classes = [IsAuthenticated]
        # Возвращаем разрешения для остальных действий
        return super().get_permissions()

    @action(detail=False, methods=['get'],
            permission_classes=settings.PERMISSIONS.user,
            url_path='me',
            url_name='me')
    def me(self, request):
        """GET-запрос на получение профиля текущего пользователя."""
        user = request.user
        # Передаем объект запроса в контекст
        serializer = UserModelSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated],
            url_name='avatar',
            url_path='me/avatar')
    def manage_avatar(self, request):
        """PUT-запрос на обновление аватара или
        DELETE-запрос на удаление аватара."""

        user = request.user

        if request.method == 'PUT':
            # Обработка обновления аватара
            serializer = AvatarUpdateSerializer(user, data=request.data,
                                                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Обработка удаления аватара
        # Удаление аватара
        avatar_exists = user.avatar and os.path.isfile(user.avatar.path)

        if avatar_exists:
            avatar_path = user.avatar.path  # Получаем путь к файлу
            os.remove(avatar_path)  # Удаляем файл
            user.avatar.delete()  # Удаляем аватар из модели
            return Response({"detail": "Аватар успешно удален."},
                            status=status.HTTP_204_NO_CONTENT)

        return Response({"detail": "Аватар не установлен или не найден."},
                        status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_name='subscriptions',
            url_path='subscriptions')
    def subscriptions(self, request):
        """
        Получение списка подписок текущего пользователя с пагинацией.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        subscribed_users = UserModel.objects.filter(
            pk__in=subscriptions.values_list('subscribed_to', flat=True)
        )
        paginator = Pagination()
        paginated_users = paginator.paginate_queryset(subscribed_users,
                                                      request)
        serializer = SubscribedUsersSerializer(paginated_users, many=True,
                                               context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated], url_path='subscribe')
    def subscribe(self, request, id=None):
        user_to_subscribe = self.get_object()
        user = request.user
        subscribed_to = get_object_or_404(UserModel, pk=id)
        if request.method == 'POST':
            # Логика для подписки
            if request.user == subscribed_to:
                return Response(
                    {'error': 'Вы не можете подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            _, created = Subscription.objects.get_or_create(
                user=user,
                subscribed_to=user_to_subscribe
            )

            if created:
                serializer = SubscribedUsersSerializer(
                    user_to_subscribe, context={'request': request})
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            return Response(
                {"detail": "Already subscribed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription.objects.filter(
            user=user, subscribed_to=user_to_subscribe
        )

        if subscription.exists():
            subscription.delete()
            return Response(
                {"detail": "Successfully unsubscribed."},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            {"detail": "Subscription does not exist."},
            status=status.HTTP_400_BAD_REQUEST
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    http_method_names = ('get',)
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = Pagination  # Настроенная пагинация
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticatedOrReadOnly, AuthorOrReadOnly)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    filterset_fields = ['author']  # Фильтрация по автору

    @action(detail=True, methods=['get'],
            permission_classes=[AllowAny], url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки для рецепта"""
        recipe = self.get_object()  # Получаем рецепт по pk
        # Строим базовый URL для рецепта
        base_url = self.request.build_absolute_uri(
            reverse('recipes-detail', kwargs={'pk': recipe.pk}))
        # Генерация короткой ссылки через метод модели
        short_hash = recipe.generate_short_url(base_url)
        short_url = (
            f"{self.request.scheme}://{self.request.get_host()}/r/{short_hash}"
        )

        return Response({"short-link": short_url}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Формирует и возвращает файл со списком покупок.
        """
        user = request.user
        # Получаем список ингредиентов, находящихся в корзине пользователя
        ingredients_data = self.get_ingredients_for_shopping_cart(user)
        if not ingredients_data:
            return Response({'error': 'Корзина пуста.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Формируем и возвращаем файл с данными
        return self.generate_shopping_cart_file(ingredients_data)

    def get_ingredients_for_shopping_cart(self, user):
        """
        Получает список ингредиентов, которые находятся в корзине пользователя,
        с подсчетом общего количества для каждого ингредиента.
        """
        # Получаем все рецепты, добавленные в корзину
        # пользователя через модель ShoppingCart
        shopping_cart_items = ShoppingCart.objects.filter(user=user)
        # Используем модель IngredientInRecipe для фильтрации по рецептам
        ingredients_data = IngredientInRecipe.objects.filter(
            recipe__in=[item.recipe for item in shopping_cart_items]
        ).values(
            'ingredient__name',  # Название ингредиента
            'ingredient__measurement_unit'  # Единица измерения
        ).annotate(
            # Агрегируем по количеству и используем 'total_quantity'
            total_amount=Sum('amount')
        ).order_by('ingredient__name')  # Упорядочиваем по названию ингредиента

        return ingredients_data

    def generate_shopping_cart_file(self, ingredients_data):
        """
        Генерирует файл с покупками на основе полученных ингредиентов.
        """
        shopping_list = "Список покупок:\n"

        for ingredient in ingredients_data:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            total_amount = ingredient['total_amount']
            shopping_list += f"{name} - {total_amount} {measurement_unit}\n"

        # Создаем ответ с файлом
        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorites(self, request, pk=None):
        """
        Добавление рецепта в избранное.
        """
        return self._add_relation(
            request=request,
            pk=pk,
            model=Favorite,
            error_message='Рецепт уже в избранном.',
            success_message='Рецепт добавлен в избранное.'
        )

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, pk=None):
        """
        Удаление рецепта из избранного.
        """
        return self._remove_relation(
            request=request,
            pk=pk,
            model=Favorite,
            success_message='Рецепт удален из избранного.'
        )

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk=None):
        """
        Добавление рецепта в корзину покупок.
        """
        return self._add_relation(
            request=request,
            pk=pk,
            model=ShoppingCart,
            error_message='Рецепт уже в корзине.',
            success_message='Рецепт добавлен в корзину.'
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """
        Удаление рецепта из корзины покупок.
        """
        return self._remove_relation(
            request=request,
            pk=pk,
            model=ShoppingCart,
            success_message='Рецепт удален из корзины.'
        )

    def _add_relation(self, request, pk, model,
                      error_message, success_message):
        """
        Общий метод для добавления рецепта в избранное или корзину.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        _, created = model.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:
            return Response({'error': error_message},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_relation(self, request, pk, model, success_message):
        """
        Общий метод для удаления рецепта из избранного или корзины.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        # Сразу удаляем запись и проверяем результат
        deleted_count, _ = model.objects.filter(user=user,
                                                recipe=recipe).delete()

        if deleted_count > 0:
            return Response({'detail': success_message},
                            status=status.HTTP_204_NO_CONTENT)

        return Response({'error': 'Рецепт не найден.'},
                        status=status.HTTP_400_BAD_REQUEST)
