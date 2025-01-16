from django.urls import path

from . import views

urlpatterns = [
    path('s/<str:short_link>/', views.redirect_short_link, name='short_link'),
]
