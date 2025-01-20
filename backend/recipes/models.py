import uuid

from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.urls import reverse

from recipes.constants import (
    USER_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    SHORT_LINK_MAX_LENGTH,
    TAG_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    COOKING_TIME_MIN_VALUE,
    AMOUNT_MIN_VALUE
)

from foodgram import settings


class UserModel(AbstractUser):
    first_name = models.CharField(max_length=USER_MAX_LENGTH,)
    last_name = models.CharField(max_length=USER_MAX_LENGTH,)

    username = models.CharField(max_length=USER_MAX_LENGTH, unique=True,
                                validators=(UnicodeUsernameValidator(),))

    email = models.EmailField(max_length=EMAIL_MAX_LENGTH,
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
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscribed_to')),
                name='prevent_self_subscription'
            )
        ]

    def clean(self):
        """Проверка на самоподписку перед сохранением."""
        if self.user == self.subscribed_to:
            raise ValidationError("Нельзя подписаться на самого себя.")

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=TAG_MAX_LENGTH,)

    slug = models.SlugField(unique=True,
                            max_length=TAG_MAX_LENGTH,)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(max_length=MEASUREMENT_UNIT_MAX_LENGTH)

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
    name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH,
                            verbose_name='Название')
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
        validators=[MinValueValidator(COOKING_TIME_MIN_VALUE)],
        verbose_name='Время приготовления (минуты)',
        help_text='Укажите время приготовления в минутах'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH, verbose_name="Короткая ссылка",
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_url()
        super().save(*args, **kwargs)

    def generate_short_url(self, base_url=None):
        """Генерация короткой ссылки"""
        return str(uuid.uuid4())[:8]

    def get_absolute_url(self):
        # Возвращаем полный URL для отображения рецепта
        return reverse('recipes-detail', kwargs={'pk': self.pk})


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ingredients_in_recipe')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(AMOUNT_MIN_VALUE)])

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
