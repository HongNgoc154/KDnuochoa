from django.contrib import admin
from django.urls import path
from . import views
from app.admin import admin_site

urlpatterns = [
    path('', views.home, name='home'),
    path('nuoc-hoa/', views.category, name='category-all'),
    path("nuoc-hoa/<slug:segment>/", views.category, name="category-segment"),
    path('product/', views.product_detail, name='product-detail'),
    path('product/<int:product_id>/', views.product_detail, name='product-detail-by-id'),
    path('thuong-hieu/', views.brand_list, name='brand-list'),
    path('thuong-hieu/<slug:slug>/', views.brand_detail, name='brand-detail'),
    path('bai-viet/', views.blog_list, name='blog-list'),
    path('bai-viet/<slug:slug>/', views.article_detail, name='article-detail'),
    path('lien-he/', views.contact_page, name='contact-page'),
    path('gio-hang/', views.cart_page, name='cart-page'),
    path('auth/', views.auth_page, name='auth-page'),
    path('tai-khoan/', views.profile_page, name='profile-page'),
    path('thanh-toan/', views.checkout_page, name='checkout-page'),
    path('logout/', views.logout_view, name='logout'),
    # path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    # path('admin/', views.admin_redirect),
    path('admin/', admin_site.urls),
     
]