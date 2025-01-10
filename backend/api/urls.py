from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UsersViewSet
)


router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
