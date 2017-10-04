from shop.models import Basket, Item

def get_basket(request):
    key = request.session.get('order_key', None)
    if key:
        print('mam key', key)
        return Basket.objects.get(session=key)
    else:
        # generate new basket
        try:
            key = int(Basket.objects.latest('id').id) + 1
            print("read key")
        except:
            key = 1
            print("except key")
        request.session['order_key'] = key
        basket = Basket(session=key)
        basket.save()
        return basket


def add_article_to_basket(basket, article, quantity):
    ex_item = Item.objects.filter(basket=basket, article=article)
    if ex_item:
        ex_item = ex_item[0]
        ex_item.quantity = ex_item.quantity + int(quantity)
        ex_item.save()
    else:
        Item(basket=basket, article=article, quantity=int(quantity), price=article.price).save()

    update_basket(basket)


def get_basket_data(basket):
    return {'total': basket.total,
            'is_open': basket.is_open,}


def update_stock(order):
    items = order.basket.items.all()
    for item in items:
        article = item.article
        article.stock = article.stock - item.quantity
        article.save()


def update_basket(basket):
    items = Item.objects.filter(basket=basket)
    basket.total = sum([item.price * item.quantity for item in items])
    basket.save()