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
        order.payment_id = payment.id
        order.save()
        for link in payment.links:
            if link.rel == "approval_url":
                # Convert to str to avoid google appengine unicode issue
                # https://github.com/paypal/rest-api-sdk-python/pull/58
                approval_url = str(link.href)
                return True, approval_url
    else:
        return False, ''

def paypal_execute(request, sc):
    success_url = request.GET.get('urlsuccess', '')
    fail_url = request.GET.get('urlfail', '')
    payment_id = request.GET.get('paymentId', '')
    payer_id = request.GET.get('PayerID', '')
    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        order = Order.objects.filter(payment_id=payment_id)
        if order:
            order = order[0]
            order.is_payed=True
            order.payer_id=payer_id
            order.save()
            url = "https://shop.djnd.si/admin/shop/order/" + str(order.id) + "/change/"
            msg = order.name + " je nekaj naročil/-a in plačal/-a je s paypalom: \n"
            for item in order.basket.items.all():
                msg += " * " + str(item.quantity) + "X " + item.article.name + "\n"
            msg += "Preveri naročilo: " + url
            if order.info:
                msg += '\n Posvetilo: ' + order.info
            sc.api_call(
              "chat.postMessage",
              channel="#danesjenovdan_si",
              text=msg
            )

            # update artickles stock
            update_stock(order)
            print("Payment execute successfully")
            return True, success_url
        else:
            return False, fail_url
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
        channel="#danesjenovdan_si",
        text="WUUHUUU nekdo nam je privoščil redno donacijo ;)"
    )
    return True, success_url

def cancel_subscription(request):
    fail_url = request.GET.get('urlfail', '')
    return fail_url



def upn(order):
    ref = 'SI00 ' + str(order.id).zfill(10)
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
