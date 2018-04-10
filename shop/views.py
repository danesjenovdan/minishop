from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core import signing

import json

from . import models

from datetime import datetime
from wkhtmltopdf.views import PDFTemplateResponse

def index(requst):
    return HttpResponse("")


@csrf_exempt
def poloznica(request):
    data = json.loads(request.body.decode('utf8'))
    bill = {}
    bill['id'] = data.get('id')
    bill['date'] = data.get('date')
    bill['price'] = data.get('price')
    bill['referencemath'] = data.get('reference')
    bill['code'] = data.get('code')
    bill['purpose'] = data.get('purpose')
    
    victim = {}
    victim['name'] = data.get('name')
    victim['address1'] = data.get('address1')
    victim['address2'] = data.get('address2')
    
    return render_to_response('poloznica.html', {'victim': victim, 'bill': bill, 'upn_id': data.get('upn_id')})


def getPDFodOrder(request, pk):
    order = get_object_or_404(models.Order, pk=signing.loads(pk))

    bill = {}
    bill['id'] = order.id
    bill['date'] = datetime.now().strftime('%d.%m.%Y')
    bill['price'] = order.basket.total
    bill['referencemath'] = order.payment_id

    if order.is_donation:
        bill['code'] = "ADCS"
        bill['purpose'] = "Donacija"
    else:
        bill['code'] = "GDSV"
        bill['purpose'] = "Položnica za račun št. " + str(order.id)
    
    address = order.address.split(',')

    victim = {}
    victim['name'] = order.name
    victim['address1'] = address[0]
    victim['address2'] = address[1] if len(address) > 1 else ''

    return PDFTemplateResponse(request=request,
                               template='poloznica.html',
                               filename='upn_djnd.pdf',
                               context={'victim': victim, 'bill': bill, 'pdf': True},
                               show_content_in_browser=True,
                               )
