from django_filters import rest_framework as filters
from django_filters import CharFilter
from django.db.models import Q

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name="tags__slug",
        to_field_name="slug"  # Сопоставление по slug
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )
    ingredient_name = CharFilter(method='filter_ingredient_name')
    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited",
                  "is_in_shopping_cart", "ingredient_name")

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию "избранное" для текущего пользователя.
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию "в корзине покупок"
        для текущего пользователя.
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_cart__user=user)
        return queryset

    def filter_ingredient_name(self, queryset, name, value):
        """
        Фильтрация рецептов по названию ингредиентов без учета порядка слов.
        """
        # Разделяем запрос на отдельные слова
        words = value.split()
        # Формируем фильтры для поиска каждого слова
        q_objects = Q()
        for word in words:
            q_objects &= Q(ingredients__name__icontains=word)
        # Применяем фильтр к queryset
        return queryset.filter(q_objects)
