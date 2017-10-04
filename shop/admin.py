from django.contrib import admin
from shop.models import Article, Basket, Order, Item, Category
from django.core.urlresolvers import reverse


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock']
    search_fields = ['name', 'stock']
    list_filter = ['name', 'stock']


class ItemInline(admin.TabularInline):
    model = Item
    fk_name = 'basket'
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'is_payed', 'payment_method', 'payment_id', 'delivery_method', 'link_to_basket']
    search_fields = ['name',]
    list_filter = ['name', 'is_payed']

    def link_to_basket(self, obj):
        link = reverse("admin:shop_basket_change", args=[obj.basket.id])
        return u'<a href="%s">Basket</a>' % (link)

    link_to_basket.allow_tags = True

class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'total', 'is_open')

    inlines = [
        ItemInline,
    ]
    search_fields = ['session']

admin.site.register(Category)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Item)
