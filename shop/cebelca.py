import requests
import random
from django.conf import settings
from datetime import datetime

class Cebelca(object): 
    def __init__(self, api_type='test'):
        self.api_key = settings.CEBELCA_KEY
        if api_type=='test':
            self.base_url = 'http://test.cebelca.biz/API?'
        else:
            self.base_url = 'https://www.cebelca.biz/API?'

    def call(self, url_args, params={}, **kwargs):
        print(self.base_url + url_args)
        r = requests.post(self.base_url + url_args,
                          data=params,
                          auth=requests.auth.HTTPBasicAuth(self.api_key, 'x'))
        return r


    def add_header(self, partner_id):
        date = datetime.now()
        data = {'date_sent': date.strftime('%d.%m.%Y'),
                'date_to_pay': (date + timedelta(days=8)).date.strftime('%d.%m.%Y'),
                'date_served': date.strftime('%d.%m.%Y'),
                'id_partner': partner_id}
        resp = self.call('_r=partner&_m=assure', data)
        return resp

    def add_partner(self, name, street, postal, city, **kwargs):
        data = {'name':name,
                'street': street,
                'postal': postal,
                'city': city}
        data.update(**kwargs)
        resp = self.call('_r=partner&_m=assure', data)
        return resp



    def add_item(self, id_invoice_sent, item_name, qty, price, mu='piece', vat=20, discount=0):
        data = {'title': item_name,
                'qty': qty,
                'mu': 'piece',
                'price': price,
                'vat': vat,
                'discount': discount,
                'id_invoice_sent': id_invoice_sent}
        resp = self.call('_r=invoice-sent-b&_m=insert-into', data)
        return resp