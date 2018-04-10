from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1%7e(ba#7x2adp6(!sx+vwn+*&uf481!rv*=91kqytk%!f2&rz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

paypalrestsdk.configure({
    "mode": "sandbox", # sandbox or live
    "client_id": "",
    "client_secret": "" })

SALT = 'somthing/stupid'

BASE_URL = 'http://localhost:8888/'

CORS_ORIGIN_ALLOW_ALL = True

CEBELCA_KEY = ""

SLACK_KEY = ""

SUPPORT_MAIL = ""

