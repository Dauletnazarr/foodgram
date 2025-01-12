from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from recipes.models import Recipe


@require_http_methods(["GET"])
def redirect_short_link(request, short_link):
    """
    Обрабатывает переход по короткой ссылке и переадресовывает
    на оригинальный рецепт.
    """
    # Ищем рецепт по короткой ссылке
    recipe = get_object_or_404(Recipe, short_link=short_link)

    # Переадресовываем на оригинальный URL рецепта
    return redirect(recipe.get_absolute_url())  # Или другой путь к рецепту
