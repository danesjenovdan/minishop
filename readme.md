Example Usage
=============

Get the basket
--------------
First get our basket and see the response:


    # this will persist the session cookies automatically for us
    session = requests.Session()

    response = session.get('http://localhost:8000/api/basket/')
    print(response.content)
    {
        "is_open": true,
        "total": "0.00",
        "order_key": "32:N3-680s8I-Imx44hqeyli5D5dgQ"
    }



Show products
--------------------------
To add a product to the basket we first need to get the available products:



    response = session.get('http://localhost:8000/api/products/')
    print(response.content)
    [
        {
            "id": 1,
            "name": "Rizle",
            "price": "3.00",
            "tax": "10.00",
            "stock": 80,
            "category": 4
        },
        {
            "id": 2,
            "name": "Donation",
            "price": "10.00",
            "tax": "0.00",
            "stock": 10000,
            "category": 3
        }
    ]
   
And categories:
    
    response = session.get('http://localhost:8000/api/categories/')
    print(response.content)
    [
        {
            "id": 3,
            "name": "Donation"
        },
        {
            "id": 4,
            "name": "Promo"
        }
    ]

Add products to the basket
--------------------------
Ok, now we want to add this to our basket:


    data = {
        "product_id": 1,
        "quantity":1
    }

    response = session.post('http://localhost:8000/api/add_to_basket/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ', json=data)

And we can see that it has been added:


    print(response.content)
    {
        "total": "3.00",
        "is_open": true,
        "items": [{"id": 23,
                   "article": {"id": 1,
                               "name": "Rizle",
                               "price": "3.00",
                               "tax": "0.00",
                               "stock": 80,
                               "category": 4}}],
        "order_key": "32:N3-680s8I-Imx44hqeyli5D5dgQ"
    }
    
    
   
Get items in basket
--------------------------

    response = session.get('http://localhost:8000/api/items/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ')
    print(response.content)
    [
        {
            "id": 5,
            "article": {
                "id": 1,
                "name": "Rizle",
                "price": "3.00",
                "tax": "10.00",
                "stock": 80,
                "category": 4
            },
            "quantity": 1
        },
        {
            "id": 6,
            "article": {
                "id": 2,
                "name": "Donation",
                "price": "10.00",
                "tax": "0.00",
                "stock": 10000,
                "category": 3
            },
            "quantity": 4
        }
    ]
    

Update or delete basket lines
-----------------------------

You can use a REST PUT and DELETE to update/delete the basket lines. So let's update the quantity for example:


    # from previous sesponse of items get item id

    id = response.json()[0]['id']

    # now update the quantity
    data = {
        "quantity": 1
    }
    response = session.put('http://localhost:8000/api/items/5/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ', data)

    # and we can see it's been updated
    print(response.content)
    {
        "id": 5,
        "article": {
            "id": 1,
            "name": "Rizle",
            "price": "3.00",
            "tax": "10.00",
            "stock": 80,
            "category": 4
        },
        "quantity": 1
    }

Now we will delete this line, it will return a 204 when it's successful:


    response = session.delete('http://localhost:8000/api/items/5/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ')
    print(response.status_code)
    204
    response = session.delete('http://localhost:8000/api/items/6/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ')
    print(response.status_code)
    204

    # we can verify that the basket is empty now
    response = session.get('http://localhost:8000/api/items/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ')
    print(response.content)
    []

Place an order (checkout)
-------------------------

When your basket is filled an you want to proceed to checkout you can do a single call with all information needed. 


### upn checkout

    
    # let's fill out the request data
    data = {
        "payment_type": "upn",
        "name": "Ivan Kunst",
        "address": "Cankarjeva ulica 15 1000 Ljubljana",
        "phone": "031031031",
        "email": "ivan@ivan.si",
        "delivery_method": "post",
    }

    # now we can place the order
    response = session.post('http://localhost:8000/api/checkout/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ', json=data)

    # and the api should give us a response with all info needed
    print (response.content)
    {
        "reference": "SI05 0000000009",
        "status": "prepared"
    } 


### paypal checkout

    
    # let's fill out the request data
    data = {
        "payment_type": "personal_takeover",
        "name": "Ivan Kunst",
        "address": "Cankarjeva ulica 15 1000 Ljubljana",
        "phone": "031031031",
        "info": "Prišu bi iskat na tobačno v sredo ob 15ih",
        "email": "ivan@ivan.si",
        "subscription": True/False, # just for donation
        "delivery_method": "takeover",
        "success_url": "http://www.success_url.si",
        "fail_url": "http://www.fail_url.com",
    }

    # now we can place the order
    response = session.post('http://localhost:8000/api/checkout/?order_key=32:N3-680s8I-Imx44hqeyli5D5dgQ', json=data)

    # and the api should give us a response with redirect url
    print (response.content)
    {
        "redirect_url": "https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-13297041LX5962133",
        "status": "prepared"
    }
    # then redirect or open this url in browser and we get next response
    {
        payment_status: "approved"
    }
