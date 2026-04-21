from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('nuoc-hoa/', views.category, name='category-all'),
    path('nuoc-hoa/<str:segment>/', views.category, name='category-segment'),
    path('product/', views.product_detail, name='product-detail'),
    path('thuong-hieu/', views.brand_list, name='brand-list'),
    path('thuong-hieu/<slug:slug>/', views.brand_detail, name='brand-detail'),
    path('bai-viet/', views.blog_list, name='blog-list'),
    path('bai-viet/<slug:slug>/', views.article_detail, name='article-detail'),
    path('lien-he/', views.contact_page, name='contact-page'),
    path('gio-hang/', views.cart_page, name='cart-page'),
]