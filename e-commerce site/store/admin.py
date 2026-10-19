from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Cart, CartItem, Order, OrderItem, NewsletterSubscriber


admin.site.site_header = 'HomeMate administration'
admin.site.site_title = 'HomeMate admin'
admin.site.index_title = 'Store and account activity'


class HomeMateUserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-last_login',)


admin.site.unregister(User)
admin.site.register(User, HomeMateUserAdmin)


@admin.register(LogEntry)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'action_flag', 'content_type', 'object_repr')
    list_filter = ('action_flag', 'content_type', 'action_time')
    search_fields = ('user__username', 'object_repr', 'change_message')
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_featured', 'is_new', 'is_active')
    list_filter = ('category', 'is_featured', 'is_new', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'total_amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'user__username')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__user__username', 'product__name')
