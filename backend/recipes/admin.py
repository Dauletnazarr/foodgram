from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count

from recipes.models import (
    IngredientInRecipe, UserModel, Recipe, Tag, Ingredient)


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    list_display = ('username', 'id', 'email', 'first_name', 'last_name',
                    'is_staff')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'measurement_unit')
    prepopulated_fields = {'measurement_unit': ('name',)}
    list_filter = ('name',)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'author', 'favorites_count')
    inlines = [IngredientInRecipeInline]
    filter_horizontal = ('tags',)
    list_filter = ('name',)

    def get_queryset(self, request):
        """
        Переопределение метода для добавления поля favorites_count
        в выборку данных.
        """
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))

    @admin.display(description='Количество добавлений в избранное')
    def favorites_count(self, obj):
        """
        Возвращает количество добавлений в избранное.
        """
        return obj.favorites_count


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    # prepopulated_fields = {'author': ('name',)}
    list_filter = ('recipe',)


admin.site.unregister(Group)
