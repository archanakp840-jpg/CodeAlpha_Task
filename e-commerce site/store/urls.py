from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('info/<slug:slug>/', views.information_page, name='information_page'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.customer_login, name='login'),
    path('accounts/staff-login/', views.staff_login, name='staff_login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
]
