import os

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import get_user_model

from djoser.conf import settings
from djoser.views import UserViewSet

from api.serializers import SubscribedUsersSerializer
from api.paginators import OwnUserPagination
from users.models import OwnUser, Subscription
from users.serializers import (
    AvatarUpdateSerializer, ChangePasswordSerializer, OwnUserCreateSerializer,
    OwnUserSerializer
)

User = get_user_model()


class MyUserViewSet(UserViewSet):
    serializer_class = OwnUserSerializer
    queryset = OwnUser.objects.all()
    permission_classes = [AllowAny]
    pagination_class = OwnUserPagination

    def create(self, request):
        """POST-запрос на создание профиля"""

        # Проверка запроса, является ли он запросом на изменение пароля
        # Если нет поля 'new_password', тогда сработает эта часть кода
        if 'new_password' in request.data:
            return self.set_password(request)

        serializer = OwnUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email
            },
            status=status.HTTP_201_CREATED
        )

    def list(self, request):
        """GET-запрос на получение списка пользователей для
        неавторизованных пользователей."""
        users = self.queryset
        paginator = self.pagination_class()  # Создаем экземпляр пагинации
        limit = request.query_params.get('limit', None)
        if limit is not None:
            paginator.page_size = int(limit)
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = OwnUserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=settings.PERMISSIONS.user,
            url_path='me',
            url_name='me')
    def me(self, request):
        """GET-запрос на получение профиля текущего пользователя."""
        user = request.user
        serializer = OwnUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated],
            url_name='avatar',
            url_path='me/avatar')
    def manage_avatar(self, request):
        """PUT-запрос на обновление аватара или
        DELETE-запрос на удаление аватара."""

        user = request.user

        if request.method == 'PUT':
            # Обработка обновления аватара
            serializer = AvatarUpdateSerializer(user, data=request.data,
                                                partial=True)

            if 'avatar' not in request.data:
                return Response({"detail": "Поле 'avatar' обязательно."},
                                status=status.HTTP_400_BAD_REQUEST)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            # Обработка удаления аватара
            if user.avatar:
                avatar_path = user.avatar.path  # Получаем путь к файлу
                if os.path.isfile(avatar_path):
                    os.remove(avatar_path)  # Удаляем файл
                    user.avatar = None  # Обнуляем поле аватара в модели
                    user.save()  # Сохраняем изменения
                    return Response({"detail": "Аватар успешно удален."},
                                    status=status.HTTP_204_NO_CONTENT)
                return Response({"detail": "Аватар не найден."},
                                status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": "Аватар не установлен."},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated],
            url_name='set_password',
            url_path='set_password')
    def set_password(self, request):
        """POST-запрос на изменение пароля пользователя."""
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            if not user.check_password(
                    serializer.validated_data['current_password']):
                return Response({"detail": "Текущий пароль неверен."},
                                status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Пароль успешно обновлен."},
                            status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_name='subscriptions',
            url_path='subscriptions')
    def subscriptions(self, request):
        """
        Получение списка подписок текущего пользователя с пагинацией.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user).select_related(
            'subscribed_to')
        subscribed_users = OwnUser.objects.filter(
            pk__in=subscriptions.values_list('subscribed_to', flat=True))

        # Получаем параметр limit из запроса
        limit = request.query_params.get('limit', None)

        # Если параметр limit есть, передаем его в пагинатор
        paginator = OwnUserPagination()
        if limit is not None:
            paginator.page_size = int(limit)

        # Пагинируем список пользователей
        paginated_users = paginator.paginate_queryset(subscribed_users,
                                                      request)
        # Сериализуем данные
        serializer = SubscribedUsersSerializer(paginated_users, many=True,
                                               context={'request': request})
        # Возвращаем ответ с пагинацией
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[IsAuthenticated],
            pagination_class=OwnUserPagination)
    def subscribe(self, request, id=None):
        """
        Подписка или отписка от пользователя.
        """
        try:
            subscribed_to = OwnUser.objects.get(pk=id)
        except OwnUser.DoesNotExist:
            return Response(
                {'error': f'Пользователь с id "{id}" не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверка на попытку подписаться на самого себя
        if request.user == subscribed_to:
            return Response(
                {'error': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            # Проверка на существующую подписку
            if Subscription.objects.filter(
                    user=request.user, subscribed_to=subscribed_to).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Создание подписки
            subscription = Subscription.objects.create(
                user=request.user, subscribed_to=subscribed_to)
            serializer = SubscribedUsersSerializer(
                subscribed_to, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            # Удаление подписки
            subscription = Subscription.objects.filter(
                user=request.user, subscribed_to=subscribed_to).first()
            if subscription:
                subscription.delete()
                return Response({'detail': 'Подписка успешно удалена.'},
                                status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST)
