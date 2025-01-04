from rest_framework.pagination import PageNumberPagination

PAGE_SIZE = 10


class OwnUserPagination(PageNumberPagination):
    page_size = PAGE_SIZE


class NoPagination(PageNumberPagination):
    page_size = None
