from urllib.request import urlopen
from urllib.parse import urlencode
import random
from django.conf import settings

class Cebelca(object): 
    def __init__(self):
        self.api_key = settings.CEBELCA_KEY

    def call(self, params={}, **kwargs):
        r = kwargs.pop('r')
        m = kwargs.pop('m')
        result = urlopen("https://%s:%s@www.cebelca.biz/API?_r=%s&_m=%s" % (self.api_key, 'x', r, m), data=urlencode(params).encode("utf-8")).read()
        return result