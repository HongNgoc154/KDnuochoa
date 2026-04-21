from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
     path('', views.home, name='home'),
    path('nuoc-hoa/', views.category, name='category-all'),
    path('nuoc-hoa/<str:segment>/', views.category, name='category-segment'),
    path('product/', views.product_detail),
]