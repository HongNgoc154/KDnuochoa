# from django.contrib import admin
from django.urls import path
from . import views
# from app.admin import admin_site

urlpatterns = [
    path('', views.home, name='home'),
    path('nuoc-hoa/', views.category, name='category-all'),
    path("nuoc-hoa/<slug:segment>/", views.category, name="category-segment"),
    path('product/', views.product_detail, name='product-detail'),
    path('product/<int:product_id>/', views.product_detail, name='product-detail-by-id'),
    path('thuong-hieu/', views.brand_list, name='brand-list'),
    path('thuong-hieu/<slug:slug>/', views.brand_detail, name='brand-detail'),
    path('bai-viet/', views.blog_list, name='blog-list'),
    path('bai-viet/<int:id>/', views.article_detail, name='article-detail'),
    path('lien-he/', views.contact_page, name='contact-page'),
    path('gio-hang/', views.cart_page, name='cart-page'),
    path('auth/', views.auth_page, name='auth-page'),
    path('auth/login/', views.login_api, name='login-api'),
    path('auth/register/', views.register_api, name='register-api'),
    path('auth/forgot-password/', views.forgot_password_api, name='forgot-password-api'),
    path('tai-khoan/', views.profile_page, name='profile-page'),
    path('thanh-toan/', views.checkout_page, name='checkout-page'),
    path('logout/', views.logout_view, name='logout'),
    path('api/apply-voucher/', views.apply_voucher_api, name='apply-voucher-api'),
    path(
        'submit-question/',
        views.submit_question,
        name='submit-question'
    ),

    # Trong app/urls.py, thêm 2 dòng này vào urlpatterns:

    path('delete-review/', views.delete_review, name='delete-review'),
    path('edit-review/',   views.edit_review,   name='edit-review'),
    # Thêm vào app/urls.py trong urlpatterns:

    path(
        "toggle-favorite/",
        views.toggle_favorite,
        name="toggle-favorite"
    ),
    path('wishlist-status/<int:product_id>/', views.get_wishlist_status, name='wishlist-status'),
    path('submit-review/', views.submit_review, name='submit-review'),
    # path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    # path('admin/', views.admin_redirect),
    # path('admin/', admin_site.urls),
     
]

