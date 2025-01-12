from django.urls import path

from recipes import views

urlpatterns = [
    path('<str:short_link>/', views.redirect_short_link,
         name='redirect_short_link'),
]
