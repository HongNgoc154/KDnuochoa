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
    path('submit-question/', views.submit_question, name='submit-question'),
    path('api/points/',         views.get_points_api,   name='points-api'),
    path('api/apply-points/',   views.apply_points_api, name='apply-points-api'),
    path('delete-review/', views.delete_review, name='delete-review'),
    path('edit-review/',   views.edit_review,   name='edit-review'),
    path('api/check-first-order/', views.check_first_order_api, name='check-first-order'),
    path("toggle-favorite/", views.toggle_favorite, name="toggle-favorite"),
    path('wishlist-status/<int:product_id>/', views.get_wishlist_status, name='wishlist-status'),
    path('submit-review/', views.submit_review, name='submit-review'),
    path('api/place-order/', views.place_order_api, name='place-order'),
    path('api/update-profile/', views.update_profile_api, name='update-profile'),

    # VNPAY
    path('api/vnpay-create/',        views.vnpay_create, name='vnpay-create'),
    path('thanh-toan/vnpay-return/', views.vnpay_return, name='vnpay-return'),

    # MOMO
    path('api/momo-create/',         views.momo_create,  name='momo-create'),
    path('thanh-toan/momo-return/',  views.momo_return,  name='momo-return'),
    path('api/momo-ipn/',            views.momo_ipn,     name='momo-ipn'),

    # ── Đơn hàng (khách) ──
    path('api/my-orders/',          views.my_orders_api,        name='my-orders-api'),
    path('api/confirm-received/',   views.confirm_received_api,  name='confirm-received'),
    path('api/cancel-order/',       views.cancel_order_api,      name='cancel-order'),

    # ── Admin ──
    path('admin-orders/',                  views.admin_orders_view,         name='admin-orders'),
    path('api/admin/update-order-status/', views.admin_update_order_status, name='admin-update-order-status'),
    path('api/admin/order-detail/',        views.admin_order_detail_api,    name='admin-order-detail'),

    # ── Admin helper: Thuộc tính & Giá trị thuộc tính ──
    path('api/admin/thuoc-tinh/',          views.api_thuoc_tinh_list,       name='api-thuoc-tinh'),
    path('api/admin/gia-tri-thuoc-tinh/',  views.api_gia_tri_thuoc_tinh,    name='api-gia-tri-thuoc-tinh'),
]