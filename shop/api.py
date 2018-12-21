from django.http import JsonResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.conf import settings
from django.core import signing
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import get_template
from django.utils.html import strip_tags

from rest_framework.views import APIView
from rest_framework import status

from datetime import datetime

from shop.models import Article, Basket, Order, Category, Item
from shop.serializers import ArticleSerializer, CategorySerializer, ItemSerializer
from shop.utils import get_basket, get_basket_data, add_article_to_basket, update_stock, update_basket
from shop.payments import paypal_checkout, paypal_execute, upn, paypal_cancel, paypal_subscriptions_checkout, execute_subscription, cancel_subscription
from shop.views import getPDFodOrder
from shop.spam_mailer import send_mail_spam

from slackclient import SlackClient

import json
# Create your views here.

sc = SlackClient(settings.SLACK_KEY)

class ProductsList(APIView):
    def get(self, request, format=None):
        #articles = Article.objects.filter(stock__gt=0)
        articles = [article for article in Article.objects.all() if article.get_stock > 0]
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
        basket = get_basket(request)
        try:
            data = json.loads(request.body.decode('utf-8'))
            product_id = data['product_id']
            quantity = data['quantity']
        except:
            return JsonResponse({"status": "Json isn't valid"})
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
            try:
                subscription = data['subscription']
            except:
                subscription = False
            success_url = data['success_url']
            fail_url = data['fail_url']
            if subscription:
                is_ok, url = paypal_subscriptions_checkout(order, success_url, fail_url)
            else:
                is_ok, url = paypal_checkout(order, success_url, fail_url)
            if is_ok:
                return JsonResponse({'status': 'prepared',
                                     'redirect_url': url})
            else:
                return JsonResponse({'status': 'failed',
                                     'info': 'status url creaton failed'})
        elif payment_type == 'upn':
            reference = upn(order)
            url = "https://shop.djnd.si/admin/shop/order/" + str(order.id) + "/change/"
            msg = order.name + " je nekaj naročil/-a in plačal/-a bo s položnico: \n"
            for item in basket.items.all():
                msg += " * " + str(item.quantity) + "X " + item.article.name + "\n"
            msg += "Preveri naročilo: " + url
            if order.info:
                msg += '\n Posvetilo: ' + order.info
            sc.api_call(
              "chat.postMessage",
              channel="#danesjenovdan_si",
              text=msg
            )
            data = {"id": order.id,
                    "upn_id": signing.dumps(order.id),
                    "date": datetime.now().strftime('%d.%m.%Y'),
                    "price": order.basket.total,
                    "reference": reference,
                    "code": "?",
                    "name": order.name,
                    "address1": order.address,
                    "address2": "",
                    "status": "prepared"}

            if order.is_donation():
                data['code'] = "ADCS"
                data['purpose'] = "Donacija"
            else:
                data['code'] = "GDSV"
                data['purpose'] = "Položnica za račun št. " + str(order.id)

            total = order.basket.total
            reference = order.payment_id
            iban = settings.IBAN.replace(' ', '')
            to_name = settings.TO_NAME.strip()
            to_address1 = settings.TO_ADDRESS1.strip()
            to_address2 = settings.TO_ADDRESS2.strip()

            html = get_template('email_poloznica.html')
            context = { 'total': total,
                        'reference': reference,
                        'iban': iban,
                        'to_address1': to_address1,
                        'to_address2': to_address2,
                        'code': data['code'],
                        'purpose': data['purpose'],
                        'bic': 'HDELSI22'}
            html_content = html.render(context)

            pdf = getPDFodOrder(None, signing.dumps(order.id)).render().content

            subject, to = 'Položnica za tvoj nakup <3', order.email
            text_content = strip_tags(html_content)

            send_mail_spam(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                to_mail=to,
                file=(
                    'racun.pdf',
                    pdf,
                    'application/pdf'
                )
            )

            #msg = EmailMultiAlternatives(subject, text_content, [to])
            #msg.attach_alternative(html_content, "text/html")
            #msg.attach('racun.pdf', pdf, 'application/pdf')
            #msg.send()

            return JsonResponse(data)
        else:
            return JsonResponse({'status': 'this payment not defined'})
    else:
        return JsonResponse({"status": "Method \"GET\" not allowed"})


def payment_execute(request):
    is_success, url = paypal_execute(request, sc)
    if is_success:
        if 'order_key' in request.session.keys():
            del request.session['order_key']

    return redirect(url)

def payment_cancel(request):
    url = paypal_cancel(request)
    return redirect(url)


def payment_subscription_execute(request):
    is_success, url = execute_subscription(request, sc)
    if is_success:
        if 'order_key' in request.session.keys():
            del request.session['order_key']

    return redirect(url)

def payment_subscription_cancel(request):
    #url = cancel_subscription(request)
    url = request.GET.get('urlfail', '')
    return redirect(url)


def clear_session(request):
    del request.session['order_key']
    return JsonResponse({'status': 'clean'})


def get_items_for_basket(request):
    html_from_view = ItemView.get(ItemView, request=request).data
    count =  sum([item['quantity'] for item in html_from_view])
    return html_from_view, count


@csrf_exempt
def send_as_email(request):
    data = json.loads(request.body.decode('utf8'))

    send_mail_spam(
        subject=data.get('title', 'untitled'),
        text_content=((data.get('email', '') + ' nam sproca: \n' ) if data.get('email', '') else '') + data.get('body', 'empty'),
        to_mail=settings.SUPPORT_MAIL,
    )

    # send_mail(
    #     data.get('title', 'untitled'),
    #     ((data.get('email', '') + ' nam sproca: \n' ) if data.get('email', '') else '') + data.get('body', 'empty'),
    #     settings.FROM_MAIL,
    #     [settings.SUPPORT_MAIL],
    #     fail_silently=False,
    # )
    return JsonResponse({"status": "sent"})



@csrf_exempt
def bussines(request):
    context = {}
    if request.POST:
        email = request.POST["email"]
        message = request.POST["message"]
        try:
            send_mail_spam(
                subject='[parlameter] Poslovna donacija',
                text_content=strip_tags('<p>Oseba z e-naslovom ' + email + ' nam želi donirati dinar. <br>Poslala nam je naslednje sporočilo: </p><p>'+ message + '</p>'),
                html_content='<p>Oseba z e-naslovom ' + email + ' nam želi donirati dinar. <br>Poslala nam je naslednje sporočilo: </p><p>'+ message + '</p>',
                to_mail='vsi@danesjenovdan.si',
            )

            # send_mail(
            #     '[parlameter] Poslovna donacija',
            #     '<p>Oseba z e-naslovom ' + email + ' nam želi donirati dinar. <br>Poslala nam je naslednje sporočilo: </p><p>'+ message + '</p>',
            #     'donacije@parlameter.si',
            #     ['info@parlametar.hr', 'info@parlameter.si', 'vsi@danesjenovdan.si'],
            #     html_message='<p>Oseba z e-naslovom ' + email + ' nam želi donirati dinar. <br>Poslala nam je naslednje sporočilo: </p><p>'+ message + '</p>',
            #     fail_silently=False,
            # )
            context["status"] = "sent"
        except:
            sc.captureException()
            context["status"] = "fail"
    else:
        context["status"] = "ni POST"

    return JsonResponse(context)