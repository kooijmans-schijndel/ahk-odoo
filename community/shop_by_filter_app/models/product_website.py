from odoo import http
from odoo import api, fields, models

class products(models.Model):

	_name = "product.name"

	names = fields.Char()


class product_count(models.Model):

	_inherit = 'product.public.category'

	count = fields.Integer()

