from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import IngredientInRecipe, OwnUser, Recipe, Tag, Ingredient


@admin.register(OwnUser)
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
    list_display = ('name', 'id', 'author')
    inlines = [IngredientInRecipeInline]
    # prepopulated_fields = {'author': ('name',)}
    filter_horizontal = ('tags',)
    list_filter = ('name',)


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    # prepopulated_fields = {'author': ('name',)}
    list_filter = ('recipe',)


# admin.site.register(Recipe, RecipeAdmin)
