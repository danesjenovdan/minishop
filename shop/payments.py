import paypalrestsdk
import logging
import urllib.parse

from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, redirect
from django.conf import settings

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
            "return_url": settings.BASE_URL + "api/payment/execute/?urlsuccess=" + s_url + "&urlfail=" + f_url,
            "cancel_url": settings.BASE_URL + "api/payment/cancel/?urlfail=" + f_url},
        "transactions": [{
            "item_list": {
                "items": get_items_dict(order.basket.items.all())},
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

def paypal_execute(request, sc):
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
        url = "http://shop.knedl.si/admin/shop/order/" + str(order[0].id) + "/change/"
        msg = "TEST :) " + order[0].name + " je neki naroču in plaču je s paypalom: \n"
        for item in order[0].basket.items.all():
            msg += " * " + str(item.quantity) + "X " + item.article.name + "\n"
        msg += "Preveri naročilo: " + url
        sc.api_call(
          "chat.postMessage",
          channel="#parlalize_notif",
          text=msg
        )

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


def paypal_subscriptions_checkout(order, success_url, fail_url):
    s_url = urllib.parse.quote(success_url, safe='~()*!.\'')
    f_url = urllib.parse.quote(fail_url, safe='~()*!.\'')
    items = order.basket.items.all()
    if items:
        item = items[0]
    else:
        print('You can\'t chackout without items?')
    billing_plan_attributes = {
        "name": 'Mesečna donacija ' + str(order.basket.total),
        "description": 'Mesečna donacija ' + str(order.basket.total),
        "merchant_preferences": {
            "auto_bill_amount": "yes",
            "cancel_url": settings.BASE_URL + "api/payment/cancel_subscription/?urlfail=" + f_url,
            "initial_fail_amount_action": "continue",
            "max_fail_attempts": "1",
            "return_url": settings.BASE_URL + "api/payment/execute_subscription/?urlsuccess=" + s_url + "&urlfail=" + f_url,
            "setup_fee": {
                "currency": "EUR",
                "value": str(order.basket.total)
            }
        },
        "payment_definitions": [
            {
                "amount": {
                    "currency": "EUR",
                    "value": str(order.basket.total)
                },
                "cycles": "0",
                "frequency": "MONTH",
                "frequency_interval": "1",
                "name": "Donation",
                "type": "REGULAR"
            }
        ],
        "type": "INFINITE"
    }
    billing_plan = paypalrestsdk.BillingPlan(billing_plan_attributes)
    if billing_plan.create():
        #print("Billing Plan [%s] created successfully" % (billing_plan))
        if billing_plan.activate():
            #print("Billing Plan [%s] activated successfully" % (billing_plan.id))
            billing_agreement = paypalrestsdk.BillingAgreement({
                "name": 'Mesečna donacija ' + str(order.basket.total),
                "description": 'Mesečna donacija ' + str(order.basket.total),
                "start_date": (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "plan": {
                    "id": billing_plan.id
                },
                "payer": {
                    "payment_method": "paypal"
                }
            })
            if billing_agreement.create():
                for link in billing_agreement.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        return True, approval_url

        else:
            #print("NI ŠLO")
            return False, ''


    else:
        # billing plan is obviously allready created :)
        print(billing_plan.error)
    return False, ''


def execute_subscription(request, sc):
    """Customer redirected to this endpoint by PayPal after payment approval
    """
    payment_token = request.GET.get('token', '')
    success_url = request.GET.get('urlsuccess', '')
    fail_url = request.GET.get('urlfail', '')
    billing_agreement_response = paypalrestsdk.BillingAgreement.execute(payment_token)
    sc.api_call(
        "chat.postMessage",
        channel="#parlalize_notif",
        text="WUUHUUU neko nam bo daju redno donacijo ;)"
    )
    return True, success_url

def cancel_subscription():
    fail_url = request.GET.get('urlfail', '')
    return fail_url



def upn(order):
    ref = 'SI05 ' + str(order.id).zfill(10)
    order.payment_id=ref
    order.save()
    items = order.basket.items.all()
    update_stock(order)
    return ref


def get_items_dict(items):
    out = []
    for item in items:
        if item.article.mergable:
            out.append({
                "name": item.article.name,
                "sku": item.article.name,
                "price": str(item.price*item.quantity),
                "currency": "EUR",
                "quantity": 1})
        else:
            out.append({
                "name": item.article.name,
                "sku": item.article.name,
                "price": str(item.price),
                "currency": "EUR",
                "quantity": item.quantity})
    return out