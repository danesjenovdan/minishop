from django.http import JsonResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from rest_framework.views import APIView
from rest_framework import status

from shop.models import Article, Basket, Order, Category, Item
from shop.serializers import ArticleSerializer, CategorySerializer, ItemSerializer
from shop.utils import get_basket, get_basket_data, add_article_to_basket, update_stock, update_basket
from shop.payments import paypal_checkout, paypal_execute, upn, paypal_cancel

import json
# Create your views here.


class ProductsList(APIView):
    def get(self, request, format=None):
        articles = Article.objects.filter(stock__gt=0)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


class CategoryList(APIView):
    def get(self, request, format=None):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class ItemView(APIView):
    def get_object(self, pk):
        try:
            return Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        basket = get_basket(request)
        items = basket.items.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        item = self.get_object(pk)
        serializer = ItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            basket = get_basket(request)
            update_basket(basket)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        item = self.get_object(pk)
        item.delete()
        basket = get_basket(request)
        update_basket(basket)
        return Response(status=status.HTTP_204_NO_CONTENT)


@csrf_exempt
def add_to_basket(request):
    if request.method == 'POST':
        print(request.session.keys())
        basket = get_basket(request)
        try:
            data = json.loads(request.body.decode('utf-8'))
            product_id = data['product_id']
            quantity = data['quantity']
        except:
            return JsonResponse({"Json isn't valid"})
        article = get_object_or_404(Article, id=product_id)

        add_article_to_basket(basket, article, quantity)

        basket_data = get_basket_data(basket)
        html_from_view, count = get_items_for_basket(request)
        basket_data['items'] = html_from_view
        basket_data['item_count'] = count

        return JsonResponse(basket_data)
    else:
        return JsonResponse({"status": "Method \"GET\" not allowed"})


def basket(request):
    basket = get_basket(request)
    basket_data = get_basket_data(basket)
    html_from_view, count = get_items_for_basket(request)
    basket_data['items'] = html_from_view
    basket_data['item_count'] = count
    return JsonResponse(basket_data)


@csrf_exempt
def checkout(request):
    if request.method == 'POST':
        basket = get_basket(request)
        if not basket.items.all():
            return JsonResponse({'status': 'error',
                                 'info': 'Your basket is empty'})
        basket.is_open = False
        basket.save()
        data = get_basket_data(basket)
        data = json.loads(request.body.decode('utf-8'))
        payment_type = data['payment_type']
        delivery_method = data['delivery_method']

        order = Order.objects.filter(basket=basket)
        if order:
            order.update(payment_method=payment_type,
                         delivery_method=delivery_method,
                         address=data.get('address', ''),
                         name=data['name'],
                         phone=data['phone'],
                         email=data['email'],
                         info=data.get('info', ''))
            order=order[0]
        else:
            order = Order(address=data['address'],
                          name=data['name'],
                          payment_method=payment_type,
                          delivery_method=delivery_method,
                          basket=basket,
                          phone=data['phone'],
                          email=data['email'],
                          payment_id='',
                          info=data.get('info', ''))
            order.save()

        if payment_type == 'paypal':
            success_url = data['success_url']
            fail_url = data['fail_url']
            is_ok, url = paypal_checkout(order, success_url, fail_url)
            if is_ok:
                return JsonResponse({'status': 'prepared',
                                     'redirect_url': url})
            else:
                return JsonResponse({'status': 'failed',
                                     'info': 'status url creaton failed'})
        elif payment_type == 'upn':
            reference = upn(order)
            del request.session['order_key']
            return JsonResponse({'status': 'prepared',
                                 'reference': reference})
        else:
            return JsonResponse({'status': 'this payment not defined'})
    else:
        return JsonResponse({"status": "Method \"GET\" not allowed"})


def payment_execute(request):
    is_success, url = paypal_execute(request)
    if is_success:
        if 'order_key' in request.session.keys():
            del request.session['order_key']

    return redirect(url)

def payment_cancel(request):
    url = paypal_cancel(request)
    return redirect(url)


def clear_session(request):
    del request.session['order_key']
    return JsonResponse({'status': 'clean'})


def get_items_for_basket(request):
    html_from_view = ItemView.get(ItemView, request=request).data
    count =  sum([item['quantity'] for item in html_from_view])
    return html_from_view, count