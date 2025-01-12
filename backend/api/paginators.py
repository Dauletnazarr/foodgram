from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    page_size = settings.PAGE_SIZE  # Значение по умолчанию
    page_size_query_param = 'limit'
    max_page_size = 100
