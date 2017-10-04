import paypalrestsdk
import logging
import urllib.parse

from django.shortcuts import get_object_or_404, redirect
from shop.models import Order
from shop.utils import update_stock


def paypal_checkout(order, success_url, fail_url):
    s_url = urllib.parse.quote(success_url, safe='~()*!.\'')
    f_url = urllib.parse.quote(fail_url, safe='~()*!.\'')
    print(s_url)
    print(f_url)
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:8000/api/payment/execute/?urlsuccess=" + s_url + "&urlfail=" + f_url,
            "cancel_url": "http://localhost:8000/api/payment/cancel/?urlfail=" + f_url},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": item.article.name,
                    "sku": item.article.name,
                    "price": str(item.price),
                    "currency": "EUR",
                    "quantity": item.quantity} for item in order.basket.items.all()]},
            "amount": {
                "total": str(order.basket.total),
                "currency": "EUR"},
            "description": "Hvala za nakup <3"}]})

    if payment.create():
        print("Payment created successfully")
        print(payment)
        order.payment_id = payment.id
        order.save()
        for link in payment.links:
            print(link)
            if link.rel == "approval_url":
                print (link.href)
                # Convert to str to avoid google appengine unicode issue
                # https://github.com/paypal/rest-api-sdk-python/pull/58
                approval_url = str(link.href)
                print('redirect to', approval_url)
                return True, approval_url
    else:
        print(payment.error)
        return False, ''

def paypal_execute(request):
    print(request)
    success_url = request.GET.get('urlsuccess', '')
    fail_url = request.GET.get('urlfail', '')
    payment_id = request.GET.get('paymentId', '')
    payer_id = request.GET.get('PayerID', '')
    print(payment_id)
    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        order = Order.objects.filter(payment_id=payment_id)
        order.update(is_payed=True, payer_id=payer_id)

        # update artickles stock
        update_stock(order[0])
        print("Payment execute successfully")
        return True, success_url
    else:
        print(payment.error)
        return False, fail_url


def paypal_cancel(request):
    fail_url = request.GET.get('urlfail', '')
    return fail_url

def upn(order):
    ref = 'SI05 ' + str(order.id).zfill(10)
    order.payment_id=ref
    order.save()
    items = order.basket.items.all()
    update_stock(order)
    return ref