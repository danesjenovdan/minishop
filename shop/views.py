from django.shortcuts import render_to_response

def poloznica(request):
    
    bill = {}
    bill['id'] = request.GET.get('id')
    bill['date'] = request.GET.get('date')
    bill['price'] = request.GET.get('price')
    bill['referencemath'] = 98 - int(bill['id']) % 97
    bill['code'] = request.GET.get('code')
    
    victim = {}
    victim['name'] = request.GET.get('name')
    victim['address1'] = request.GET.get('address1')
    victim['address2'] = request.GET.get('address2')
    
    return render_to_response('poloznica.html', {'victim': victim, 'bill': bill})