from rest_framework.pagination import PageNumberPagination
from foodgram.settings import PAGE_SIZE


class UserModelPagination(PageNumberPagination):
    page_size = PAGE_SIZE  # Значение по умолчанию
    page_size_query_param = 'limit'
    max_page_size = 100
