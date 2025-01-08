from rest_framework.permissions import BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Разрешает доступ только автору объекта
    для операций изменения (PUT/PATCH/DELETE),
    для всех остальных - доступ только на чтение (GET).
    """
    def has_object_permission(self, request, view, obj):
        # Используем базовую проверку для безопасных методов
        if request.method == 'GET':
            return True

        if request.method in ['POST']:
            return request.user and request.user.is_authenticated

        # Для методов PATCH и DELETE проверяем права на объект
        if request.method in ('PATCH', 'DELETE'):
            # Разрешаем редактирование или удаление, если пользователь автор
            return request.user.is_authenticated and obj.author == request.user
