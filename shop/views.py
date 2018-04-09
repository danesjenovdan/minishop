from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt

import json

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
    
    victim = {}
    victim['name'] = data.get('name')
    victim['address1'] = data.get('address1')
    victim['address2'] = data.get('address2')
    
    return render_to_response('poloznica.html', {'victim': victim, 'bill': bill})