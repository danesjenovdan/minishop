import requests
import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from datetime import datetime, timedelta

class Cebelca(object): 
    def __init__(self, api_type='test'):
        self.api_key = settings.CEBELCA_KEY
        if api_type=='test':
            self.base_url = 'http://test.cebelca.biz/API'
        else:
            self.base_url = 'https://www.cebelca.biz/API'

        self.partner = None
        self.invoice_id = None

    def call(self, url_args, params={}, **kwargs):
        print(self.base_url + url_args)
        r = requests.post(self.base_url + url_args,
                          data=params,
                          auth=requests.auth.HTTPBasicAuth(self.api_key, 'x'))
        return r


    def add_partner(self, name, street, postal, city, **kwargs):
        data = {'name':name,
                'street': street,
                'postal': postal,
                'city': city}
        data.update(**kwargs)
        resp = self.call('?_r=partner&_m=assure', data)
        if resp.status_code == 200:
            self.partner = resp.json()[0][0]['id']
            return True, None
        else:
            return False, resp.content


    def add_header(self):
        if self.partner:
            date = datetime.now()
            data = {'date_sent': date.strftime('%d.%m.%Y'),
                    'date_to_pay': (date + timedelta(days=8)).strftime('%d.%m.%Y'),
                    'date_served': date.strftime('%d.%m.%Y'),
                    'id_partner': self.partner}
            resp = self.call('?_r=invoice-sent&_m=insert-into', data)
            if resp.status_code == 200:
                self.invoice_id = resp.json()[0][0]['id']
                return True, None
            else:
                return False, resp.content
        else:
            return False, 'First create a partner'


    def add_item(self, item_name, qty, price, mu='kos', vat=20, discount=0):
        if self.invoice_id:
            data = {'title': item_name,
                    'qty': qty,
                    'mu': 'kos',
                    'price': price,
                    'vat': vat,
                    'discount': discount,
                    'id_invoice_sent': self.invoice_id}
            resp = self.call('?_r=invoice-sent-b&_m=insert-into', data)
            if resp.status_code == 200:
                print(resp.content)
                return True, resp
            else:
                return False, resp.content
        else:
            return False, 'First create an invoice'


    def set_invoice_paid(self, id_payment_method, amount):
        # gotovina 2, paypal 5
        if self.invoice_id:
            data = {'date_of': datetime.now().strftime('%d.%m.%Y'),
                    'amount': amount,
                    'id_payment_method': id_payment_method,
                    'id_invoice_sent': self.invoice_id}
            resp = self.call('?_r=invoice-sent-p&_m=mark-paid', data)
            if resp.status_code == 200:
                print(resp.content)
                return True, resp
            else:
                return False, resp.content
        else:
            return False, 'First create an invoice'

    def finalize_invoice(self, title=''):
        if self.invoice_id:
            data = {'id': self.invoice_id,
                    'title': title,
                    'doctype': 0}
            resp = self.call('?_r=invoice-sent&_m=finalize-invoice-2015', data)
            if resp.status_code == 200:
                print(resp.content)
                return True, resp
            else:
                return False, resp.content
        else:
            return False, 'First create an invoice'


    def get_pdf(self):
        if self.invoice_id:
            resp = requests.get(self.base_url + '-pdf?id='+str(self.invoice_id)+'&format=PDF&doctitle=Ra%C4%8Dun%20%C5%A1t.&lang=si&disposition=inline&res=invoice-sent&preview=0',
                             auth=requests.auth.HTTPBasicAuth(self.api_key, 'x'))
            if resp.status_code == 200:
                return True, resp.content
            else:
                return False, resp.content
        else:
            return False, 'First create an invoice'

    def send_mail(self, email, title, body):
        print("send mail")
        pdf = self.get_pdf()
        if pdf[0]:
            subject, from_email, to = title, settings.FROM_MAIL, email
            text_content = strip_tags(body)
            html_content = body
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.attach('racun.pdf', pdf[1], 'application/pdf')
            msg.send()

            return True, 'Sent'
        else:
            return False, 'Cannot get pdf'

def test():
    c = Cebelca(api_type="prod")
    c.add_partner('name', "street", "1000", "Ljubljana")
    c.add_header()
    c.add_item("rizle2", 1, 2, vat=0)
    c.set_invoice_paid(5, 2)
    c.finalize_invoice()
