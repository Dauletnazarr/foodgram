from django.contrib.auth import get_user_model

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import (
    Ingredient, IngredientInRecipe, OwnUser, Recipe, RecipeStatus, Tag
)
from users.serializers import OwnUserSerializer

User = get_user_model()


class TagSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
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

    def to_representation(self, instance):
        """
        Переопределение метода to_representation
        для использования IngredientInRecipeReadSerializer.
        """
        read_serializer = IngredientInRecipeReadSerializer(
            instance, context=self.context)
        return read_serializer.data


class RecipeReadSerializer(serializers.ModelSerializer):
    # Поля для работы с изображением и автором рецепта
    image = Base64ImageField(read_only=True)
    author = OwnUserSerializer(read_only=True)

    # Используем IngredientInRecipeReadSerializer для вложенных ингредиентов
    ingredients = IngredientInRecipeReadSerializer(many=True, read_only=True)

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
        if not request or not request.user.is_authenticated:
            return False
        return RecipeStatus.objects.filter(
            user=request.user, recipe=obj, status='favorite').exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяем, находится ли рецепт в корзине покупок текущего пользователя.
        Возвращаем False для анонимных пользователей.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return RecipeStatus.objects.filter(
            user=request.user, recipe=obj, status='shopping_cart').exists()


class RecipeSerializer(serializers.ModelSerializer):
    # Поля для работы с изображением и автором рецепта
    image = Base64ImageField(required=True)
    author = OwnUserSerializer(read_only=True)

    # Вложенный сериализатор для ингредиентов
    ingredients = IngredientInRecipeSerializer(many=True, required=True)

    # Теги, связанные с рецептом
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        ]

    def validate(self, data):
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

        image = data.get('image', None)
        if image is None or image == '':
            raise serializers.ValidationError({
                "image": "Поле 'image' не может быть пустым."
            })

        cooking_time = data.get('cooking_time', 0)
        if cooking_time < 1:
            raise serializers.ValidationError({
                "cooking_time": (
                    "Время приготовления должно быть не меньше 1 минуты.")
            })

        return data

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

    def update(self, instance, validated_data):
        """
        Метод для обновления рецепта и связанных объектов.
        """
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        # Обновляем основную информацию рецепта
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()

        # Обновляем теги
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Обновляем ингредиенты
        if ingredients_data is not None:
            IngredientInRecipe.objects.filter(recipe=instance).delete()
            self._create_recipe_ingredients(instance, ingredients_data)

        return instance

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

        if ingredient_instances:
            IngredientInRecipe.objects.bulk_create(ingredient_instances)
        else:
            print("No ingredient instances to create")

    def to_representation(self, instance):
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        representation = read_serializer.data

        # Обрабатываем ингредиенты с учетом количества
        ingredients = IngredientInRecipe.objects.filter(recipe=instance)
        representation['ingredients'] = IngredientInRecipeReadSerializer(
            ingredients, many=True).data

        return representation


class SubscribedUsersSerializer(serializers.ModelSerializer):
    recipes = RecipeReadSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = OwnUser
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar']

    def get_recipes_count(self, obj):
        """
        Метод для подсчёта количества рецептов у пользователя.
        """
        return obj.recipes.count()

    def to_representation(self, instance):
        """
        Переопределяем метод to_representation,
        чтобы передавать только определенные поля из RecipeReadSerializer.
        """
        representation = super().to_representation(instance)
        recipes_limit = self.context[
            'request'].query_params.get('recipes_limit')

        # Изменим поля в 'recipes', передавая только нужные поля
        if 'recipes' in representation:
            # Задаем список нужных полей,
            # которые мы хотим получить из RecipeReadSerializer
            # Пример нужных полей
            fields_to_include = ['id', 'name', 'image', 'cooking_time']
            recipes_data = representation['recipes']

            # Применяем фильтрацию для каждого рецепта
            filtered_recipes = []
            for recipe in recipes_data:
                filtered_recipe = {
                    field: recipe.get(field) for field in fields_to_include}
                filtered_recipes.append(filtered_recipe)

            if recipes_limit:
                filtered_recipes = filtered_recipes[:int(recipes_limit)]

            representation['recipes'] = filtered_recipes

        return representation
