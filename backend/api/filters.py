from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name="tags__slug",
        to_field_name="slug"  # Сопоставление по slug
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию "избранное" для текущего пользователя.
        """
        user = self.request.user
        # Если рецепты должны быть в избранном
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset  # Если пользователь не аутентифицирован,
        # просто возвращаем все рецепты

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию "в корзине покупок"
        для текущего пользователя.
        """
        user = self.request.user
        if value and user.is_authenticated:  # Если рецепты должны быть
            # в корзине покупок
            return queryset.filter(in_cart__user=user)
        return queryset  # Если пользователь не аутентифицирован,
        # просто возвращаем все рецепты
