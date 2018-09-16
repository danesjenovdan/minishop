from django.conf.urls import url
from shop.api import (ProductsList, CategoryList, ItemView, add_to_basket,
                      basket, checkout, payment_execute, payment_cancel,
                      clear_session, payment_subscription_execute, cancel_subscription,
                      send_as_email, bussines)

urlpatterns = [
    url(r'^products/', ProductsList.as_view()),
    url(r'^categories/', CategoryList.as_view()),
    url(r'^items/(?P<pk>\d+)/', ItemView.as_view()),
    url(r'^items/', ItemView.as_view()),
    url(r'^add_to_basket/', add_to_basket),
    url(r'^basket/', basket),
    url(r'^checkout/', checkout),
    url(r'^payment/execute/', payment_execute),
    url(r'^payment/cancel/', payment_cancel),
    url(r'^payment/execute_subscription/', payment_subscription_execute),
    url(r'^payment/cancel_subscription/', cancel_subscription),
    url(r'^clear', clear_session),
    url(r'^send_as_email', send_as_email),
    url(r'^bussines', bussines)
    ]
