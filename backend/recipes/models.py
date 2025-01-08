import hashlib

from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.urls import reverse


from recipes.constants import (
    MAX_LENGTH_32, MAX_LENGTH_64, MAX_LENGTH_128,
    MAX_LENGTH_150, MAX_LENGTH_254
)
from foodgram import settings

# КОНСТАНТЫ ПОТОМ ДОДЕЛАЮ :)

# from recipes.constants import (
#     USER_USERNAME_MAX_LENGTH,
#     USER_EMAIL_MAX_LENGTH,
#     RECIPE_TITLE_MAX_LENGTH,
#     RECIPE_DESCRIPTION_MAX_LENGTH,
#     INGREDIENT_NAME_MAX_LENGTH,
# )


class UserModel(AbstractUser):
    first_name = models.CharField(max_length=MAX_LENGTH_150,)
    last_name = models.CharField(max_length=MAX_LENGTH_150,)

    username = models.CharField(max_length=MAX_LENGTH_150, unique=True,
                                validators=(UnicodeUsernameValidator(),))

    email = models.EmailField(max_length=MAX_LENGTH_254,
                              unique=True)
    avatar = models.ImageField(upload_to='users/avatars/',
                               blank=True,
                               null=True,)

    # Используем email в качестве имени пользователя для авторизации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='subscriptions',
                             on_delete=models.CASCADE)

    subscribed_to = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      related_name='subscribers',
                                      on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'subscribed_to')

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'

    def save(self, *args, **kwargs):
        if self.user == self.subscribed_to:
            raise ValidationError('Вы не можете подписаться на самого себя!')
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_32,)

    slug = models.SlugField(unique=True,
                            max_length=MAX_LENGTH_32,)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_128)
    measurement_unit = models.CharField(max_length=MAX_LENGTH_64)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='in_cart')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_user_recipe')]

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class Recipe(models.Model):
    author = models.ForeignKey(
        UserModel, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    name = models.CharField(max_length=MAX_LENGTH_64, verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=False
    )
    text = models.TextField(verbose_name='Описание',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag,)
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (минуты)',
        help_text='Укажите время приготовления в минутах'
    )
    short_link = models.CharField(
        max_length=128, null=True, blank=True, verbose_name="Короткая ссылка"
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Генерация базового URL для рецепта
        base_url = reverse('recipes-detail', kwargs={'pk': self.pk})
        # Генерация короткой ссылки
        self.short_link = self.generate_short_url(base_url)
        # Сохраняем объект
        super().save(*args, **kwargs)

    def generate_short_url(self, base_url):
        """Генерация короткой ссылки на основе id рецепта"""
        hash_object = hashlib.md5(base_url.encode())
        short_hash = hash_object.hexdigest()[:8]  # Сокращаем хеш до 8 символов
        return short_hash


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингредиенты в Рецептах'
        verbose_name_plural = 'Ингредиенты в Рецептах'

    def __str__(self):
        return f'Ингредиент в рецепте({self.recipe}-{self.ingredient})'


class Favorite(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_fav_user_recipe')]

    def __str__(self):
        return f'Рецепт "{self.recipe}" в избранном у {self.user}'
