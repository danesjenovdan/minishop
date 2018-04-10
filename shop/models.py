from django.db import models
from behaviors.behaviors import Timestamped

# Create your models here.

class Category(Timestamped):
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name


class Article(Timestamped):
	name = models.CharField(max_length=64)
	category = models.ForeignKey(Category, null=True, blank=True)
	upc = models.CharField(max_length=64, null=True, blank=True)
	price = models.DecimalField(decimal_places=2, max_digits=10)
	tax = models.DecimalField(decimal_places=2, max_digits=10)
	stock = models.IntegerField(default=0)
	image = models.ImageField(upload_to='images/', height_field=None, width_field=None, max_length=1000, null=True, blank=True)
	mergable = models.BooleanField(default=False)

	def __str__(self):
		return self.name


class Basket(Timestamped):
	session = models.CharField(max_length=64)
	articles = models.ManyToManyField(Article, through='Item')
	total = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
	is_open = models.BooleanField(default=True)


class Item(Timestamped):
	article = models.ForeignKey(Article)
	basket = models.ForeignKey(Basket, related_name="items")
	price =  models.DecimalField(decimal_places=2, max_digits=10)
	quantity = models.IntegerField(default=1)
	def __str__(self):
		return "item " + self.article.name

class Order(Timestamped):
	basket = models.ForeignKey(Basket, related_name='order')
	name = models.CharField(max_length=64)
	address = models.CharField(max_length=256)
	phone = models.CharField(max_length=64, null=True, blank=True)
	is_payed = models.BooleanField(default=False)
	payment_id = models.CharField(max_length=64, null=True, blank=True)
	payer_id = models.CharField(max_length=64, null=True, blank=True)
	payment_method = models.CharField(max_length=64, null=True, blank=True)
	delivery_method = models.CharField(max_length=64, null=True, blank=True)
	email = models.CharField(max_length=64, null=True, blank=True)
	info = models.CharField(max_length=256, null=True, blank=True)
	is_sent = models.BooleanField(default=False)

	def __str__(self):
		return "order of:" + self.name

	def is_donation(self):
		return bool(self.basket.items.filter(article__name__icontains="donacija"))

