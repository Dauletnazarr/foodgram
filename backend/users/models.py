from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator

from users.constants import (
    MAX_LENGTH_20, MAX_LENGTH_32, MAX_LENGTH_64, MAX_LENGTH_128,
    MAX_LENGTH_150, MAX_LENGTH_254
)
from foodgram import settings


class OwnUser(AbstractUser):
    first_name = models.CharField(max_length=MAX_LENGTH_150, blank=False)
    last_name = models.CharField(max_length=MAX_LENGTH_150, blank=False)

    username = models.CharField(max_length=MAX_LENGTH_150, unique=True,
                                blank=False,
                                validators=(UnicodeUsernameValidator(),))

    email = models.EmailField(max_length=MAX_LENGTH_254, blank=False,
                              unique=True)
    is_subscribed = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='users/avatars/',
                               blank=True,
                               null=True,)

    # Используем email в качестве имени пользователя для авторизации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='subscriptions',
                             on_delete=models.CASCADE)

    subscribed_to = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      related_name='subscribers',
                                      on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'subscribed_to')


class Tag(models.Model):
    name = models.CharField(blank=False,
                            max_length=MAX_LENGTH_32,)

    slug = models.SlugField(blank=False,
                            unique=True,
                            max_length=MAX_LENGTH_32,)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return str(self.name)[:MAX_LENGTH_32]


class Ingredient(models.Model):
    name = models.CharField(blank=False, max_length=MAX_LENGTH_128)
    measurement_unit = models.CharField(blank=False, max_length=MAX_LENGTH_64)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='in_cart')

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class Recipe(models.Model):
    author = models.ForeignKey(
        OwnUser, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    name = models.CharField(max_length=MAX_LENGTH_64, verbose_name='Название')
    image = models.ImageField(
        blank=False,
        upload_to='recipes/images/',
        null=False
    )
    text = models.TextField(verbose_name='Описание',)
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, blank=False,)
    shopping_cart = models.ManyToManyField(OwnUser, through=ShoppingCart)
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (минуты)',
        help_text='Укажите время приготовления в минутах'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeStatus(models.Model):
    STATUS_CHOICES = [
        ('favorite', 'Favorite'),
        ('shopping_cart', 'Shopping Cart'),
    ]

    user = models.ForeignKey(OwnUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, max_length=MAX_LENGTH_20)

    class Meta:
        unique_together = ('user', 'recipe', 'status')


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['recipe']
        verbose_name = 'Ингредиенты в Рецептах'
        verbose_name_plural = 'Ингредиенты в Рецептах'


class Favorite(models.Model):
    user = models.ForeignKey(OwnUser, on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='in_favorites')

    class Meta:
        unique_together = ('user', 'recipe')
