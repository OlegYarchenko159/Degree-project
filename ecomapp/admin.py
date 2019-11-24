from django.contrib import admin
from .models import Category, Brand, Product, CartItem, Cart, Order


def make_payed(modeladmin, request, queryset):
    queryset.update(status='Оплачен')


def make_in_progress(modeladmin, request, queryset):
    queryset.update(status='Выполняется')


make_payed.short_description = 'Пометить как оплаченые'
make_in_progress.short_description = 'Пометить как в процессе выполнения'


class OrderAdmin(admin.ModelAdmin):
    list_filter = ['status']
    actions = [make_payed, make_in_progress]


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Order, OrderAdmin)



