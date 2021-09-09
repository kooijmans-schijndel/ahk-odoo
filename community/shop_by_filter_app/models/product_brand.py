from odoo import api, fields, models, _

class product_brand(models.Model):

	_name = "product.brand"

	name = fields.Char(string="Name", required=True)
	image = fields.Binary(string="Logo", required=True)
	sequence = fields.Char(string="Sequence", required=True)
	count = fields.Integer()

class product_product(models.Model):

	_inherit = "product.template"
	
	brands = fields.Many2one('product.brand', string="Brand")
