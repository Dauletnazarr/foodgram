from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms import ValidationError
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart,
    Subscription, Tag, UserModel)

User = get_user_model()


class UserModelSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = UserModel  # Замените на вашу модель пользователя
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        """
        Метод для проверки, подписан ли текущий
        пользователь на данного пользователя.
        """
        return bool(
            self.context.get('request') and (
                self.context['request'].user.is_authenticated
            ) and Subscription.objects.filter(
                user=self.context['request'].user,
                subscribed_to=obj
            ).exists()
        )


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = UserModel
        fields = ['avatar']

    def validate(self, attrs):
        """Проверка, что аватар не является null или пустым."""
        avatar = attrs.get('avatar')

        if avatar is None:
            raise ValidationError({"avatar": "Поле 'avatar' обязательно."})

        if isinstance(avatar, str) and not avatar.strip():
            raise ValidationError(
                {"avatar": "Поле 'avatar' не может быть пустым."})

        return attrs


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'  # This ensures the correct reference
    )
    amount = serializers.IntegerField(
        min_value=1,
        required=True,
        error_messages={"min_value": "Количество должно быть не меньше 1."},)

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'amount']


class RecipeReadSerializer(serializers.ModelSerializer):
    # Поля для работы с изображением и автором рецепта
    image = Base64ImageField(read_only=True)
    author = UserModelSerializer(read_only=True)

    # Используем IngredientInRecipeReadSerializer для вложенных ингредиентов
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        read_only=True,
        source='ingredients_in_recipe'
    )

    # Теги возвращаются с использованием имени
    tags = TagSerializer(many=True)

    # Добавляем новые поля
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        """
        Проверяем, добавил ли текущий пользователь рецепт в избранное.
        Возвращаем False для анонимных пользователей.
        """
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, recipe=obj,).exists())

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяем, находится ли рецепт в корзине покупок текущего пользователя.
        Возвращаем результат логического выражения.
        """
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj,).exists())


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""
    image = Base64ImageField(required=True)
    author = UserModelSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        ]

    def validate(self, data):
        """
        Общая валидация данных рецепта.
        """
        # Проверка ингредиентов
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                "ingredients": "Поле 'ingredients' не может быть пустым."
            })

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                "ingredients": "Ингредиенты не должны повторяться."
            })

        # Проверка тегов
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({
                "tags": "Поле 'tags' не может быть пустым."
            })

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                "tags": "Теги не должны повторяться."
            })

        cooking_time = data.get('cooking_time', 0)
        if cooking_time < 1:
            raise serializers.ValidationError({
                "cooking_time": (
                    "Время приготовления должно быть не меньше 1 минуты.")

            })

        return data

    def validate_image(self, value):
        """
        Проверка наличия картинки.
        Запускается только если поле 'image' присутствует в запросе.
        """
        if not value:
            raise serializers.ValidationError(
                "Поле 'image' не может быть пустым.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Метод для создания рецепта и связанных объектов.
        """
        # Извлекаем ингредиенты и теги
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        # Создаем рецепт
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        # Устанавливаем теги
        recipe.tags.set(tags_data)

        # Создаем ингредиенты для рецепта
        self._create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Метод для обновления рецепта и связанных объектов.
        """
        # Извлекаем данные для тегов и ингредиентов,
        # так как они требуют дополнительных манипуляций
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        # Если переданы теги, обновляем их
        instance.tags.set(tags_data)
        # Обновляем ингредиенты, если они переданы
        # Удаляем старые ингредиенты
        instance.ingredients.clear()
        # Создаем новые ингредиенты
        self._create_recipe_ingredients(instance, ingredients_data)

        # Обновляем остальные поля с использованием стандартного метода
        return super().update(instance, validated_data)

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        """
        Вспомогательный метод для создания связей ингредиентов с рецептом.
        """
        ingredient_instances = []
        for ingredient_data in ingredients_data:
            ingredient_instance = ingredient_data['ingredient']
            ingredient_instances.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_instance,
                amount=ingredient_data['amount']
            ))
        IngredientInRecipe.objects.bulk_create(ingredient_instances)

    def to_representation(self, instance):
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        representation = read_serializer.data
        return representation


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткой информации о рецепте.
    """
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscribedUsersSerializer(UserModelSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = UserModel  # Модель, которая будет сериализована (UserModel)
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count', 'avatar']

    def get_recipes_count(self, obj):
        """
        Метод для подсчёта количества рецептов у пользователя.
        """
        return obj.recipes.count()

    def get_recipes(self, obj):
        """
        Метод для получения рецептов с ограничением по числу,
        используя параметр recipes_limit.
        """
        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')

        recipes_query = obj.recipes.all()
        if recipes_limit:
            recipes_query = recipes_query[:int(recipes_limit)]

        recipes_data = RecipeReadSerializer(recipes_query, many=True).data

        fields_to_include = ['id', 'name', 'image', 'cooking_time']
        filtered_recipes = [
            {field: recipe.get(field) for field in fields_to_include}
            for recipe in recipes_data
        ]

        return filtered_recipes
