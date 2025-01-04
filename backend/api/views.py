from django.http import HttpResponse
from django.urls import reverse

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

import hashlib

from api.paginators import OwnUserPagination
from api.serializers import (
    TagSerializer, IngredientSerializer, RecipeSerializer
)
from users.models import (
    Favorite, Ingredient, IngredientInRecipe, ShoppingCart, Tag, Recipe
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class IngredientViewSet(viewsets.ModelViewSet):
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
    pagination_class = OwnUserPagination  # Настроенная пагинация
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['author']  # Фильтрация по автору

    def perform_update(self, serializer):
        # Проверяем, что текущий пользователь является автором рецепта
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("Вы не можете обновить чужой рецепт.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        # Получаем рецепт, который пытаются удалить
        recipe = self.get_object()

        # Проверяем, является ли текущий пользователь автором рецепта
        if recipe.author != request.user:
            raise PermissionDenied("Вы не можете удалить чужой рецепт.")

        # Если автор совпадает, вызываем стандартное удаление
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'],
            permission_classes=[AllowAny], url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки для рецепта"""
        recipe = self.get_object()  # Получаем рецепт по pk

        # Здесь создаем короткую ссылку, например, с помощью хеширования
        short_link = self.generate_short_url(recipe)

        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    def generate_short_url(self, recipe):
        """Генерация короткой ссылки на основе id рецепта"""
        base_url = self.request.build_absolute_uri(reverse(
            'recipes-detail', kwargs={'pk': recipe.pk}))
        hash_object = hashlib.md5(base_url.encode())
        short_hash = hash_object.hexdigest()[:8]  # Сокращаем хеш до 8 символов
        short_url = (
            f"{self.request.scheme}://"
            f"{self.request.get_host()}/r/{short_hash}"
        )
        return short_url

    def paginate_queryset(self, queryset):
        """
        Переопределяем метод пагинации, чтобы поддерживать параметр 'limit'
        """
        # Получаем параметр 'limit'
        limit = self.request.query_params.get('limit')
        if limit is not None:
            self.pagination_class.page_size = int(limit)
        return super().paginate_queryset(queryset)

    def get_queryset(self):
        """
        Этот метод фильтрует рецепты по тегам,
        автору и поддерживает параметр 'limit'.
        """
        queryset = super().get_queryset()

        # Фильтрация по тегам
        # Получаем список тегов из запроса
        tags = self.request.query_params.getlist('tags')
        if tags:
            # Фильтруем рецепты, которые содержат хотя бы
            # один тег из списка (НЕ пересечение)
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset

    @action(detail=True, methods=['post', 'delete'],
            url_path='shopping_cart', permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """
        Добавление или удаление рецепта из корзины.
        """
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'error': 'Рецепт не найден.'}, status=404)

        user = request.user

        if request.method == 'POST':
            # Проверяем, есть ли рецепт в корзине
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'error': 'Рецепт уже в корзине.'}, status=400)

            ShoppingCart.objects.create(user=user, recipe=recipe)
            response_data = {
                "id": recipe.id,
                "name": recipe.name,
                "image": (
                    request.build_absolute_uri(
                        recipe.image.url) if recipe.image else None),
                "cooking_time": recipe.cooking_time
            }
            return Response(response_data, status=201)

        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(
                user=user, recipe=recipe).first()
            if cart_item:
                cart_item.delete()
                return Response({'detail': 'Рецепт удален из корзины.'},
                                status=204)

            return Response({'error': 'Рецепт не найден в корзине.'},
                            status=400)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Формирует и возвращает файл со списком покупок.
        """
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(
            user=user).select_related('recipe')

        if not shopping_cart.exists():
            return Response({'error': 'Корзина пуста.'}, status=400)

        # Формируем содержимое файла
        shopping_list = "Список покупок:\n"
        ingredient_totals = {}

        for cart_item in shopping_cart:
            recipe = cart_item.recipe
            recipe_ingredients = IngredientInRecipe.objects.filter(
                recipe=recipe).select_related('ingredient')

            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient
                name = ingredient.name
                measurement_unit = ingredient.measurement_unit
                amount = recipe_ingredient.amount

                # Суммируем количество одинаковых ингредиентов
                if name in ingredient_totals:
                    ingredient_totals[name]['amount'] += amount
                else:
                    ingredient_totals[name] = {
                        'amount': amount, 'measurement_unit': measurement_unit}

        # Формируем итоговый список
        for name, details in ingredient_totals.items():
            shopping_list += (
                f"{name} - {details['amount']} {details['measurement_unit']}\n"
            )

        # Создаем ответ с файлом
        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(detail=True, methods=['post', 'delete'],
            url_path='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """
        Добавление или удаление рецепта из избранного.
        """
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'error': 'Рецепт не найден.'},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            # Проверка, если рецепт уже в избранном
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'error': 'Рецепт уже добавлен в избранное.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Добавляем рецепт в избранное
            Favorite.objects.create(user=user, recipe=recipe)

            # Формируем ответ с нужными полями
            response_data = {
                "id": recipe.id,
                "name": recipe.name,
                "image": request.build_absolute_uri(recipe.image.url),
                "cooking_time": recipe.cooking_time,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Удаление рецепта из избранного
            favorite_item = Favorite.objects.filter(
                user=user, recipe=recipe).first()
            if favorite_item:
                favorite_item.delete()
                return Response(
                    {'detail': 'Рецепт успешно удален из избранного.'},
                    status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Рецепт отсутствует в избранном.'},
                status=status.HTTP_400_BAD_REQUEST)
