from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrReadOnly(BasePermission):
    """
    Разрешение, позволяющее редактировать объект только автору.
    Остальным пользователям доступен только просмотр.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
