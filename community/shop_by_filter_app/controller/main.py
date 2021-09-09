import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression

_logger = logging.getLogger(__name__)

PPG = 20 
PPR = 4 

class TableCompute(object):

	def __init__(self):
		self.table = {}

	def _check_place(self, posx, posy, sizex, sizey, ppr):
		res = True
		for y in range(sizey):
			for x in range(sizex):
				if posx + x >= ppr:
					res = False
					break
				row = self.table.setdefault(posy + y, {})
				if row.setdefault(posx + x) is not None:
					res = False
					break
			for x in range(ppr):
				self.table[posy + y].setdefault(x, None)
		return res

	
	def process(self, products, ppg=20, ppr=4):
		# Compute products positions on the grid
		minpos = 0
		index = 0
		maxy = 0
		x = 0
		for p in products:
			x = min(max(p.website_size_x, 1), ppr)
			y = min(max(p.website_size_y, 1), ppr)
			if index >= ppg:
				x = y = 1

			pos = minpos
			while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
				pos += 1
			# if 21st products (index 20) and the last line is full (ppr products in it), break
			# (pos + 1.0) / ppr is the line where the product would be inserted
			# maxy is the number of existing lines
			# + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
			# and to force python to not round the division operation
			if index >= ppg and ((pos + 1.0) // ppr) > maxy:
				break

			if x == 1 and y == 1:   # simple heuristic for CPU optimization
				minpos = pos // ppr

			for y2 in range(y):
				for x2 in range(x):
					self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
			self.table[pos // ppr][pos % ppr] = {
				'product': p, 'x': x, 'y': y,
				'ribbon': p.website_ribbon_id,
			}
			if index <= ppg:
				maxy = max(maxy, y + (pos // ppr))
			index += 1

		# Format table according to HTML needs
		rows = sorted(self.table.items())
		rows = [r[1] for r in rows]
		for col in range(len(rows)):
			cols = sorted(rows[col].items())
			x += len(cols)
			rows[col] = [r[1] for r in cols if r[1]]

		return rows

class WebsiteSale(http.Controller):

	def _get_pricelist_context(self):
		pricelist_context = dict(request.env.context)
		pricelist = False
		if not pricelist_context.get('pricelist'):
			pricelist = request.website.get_current_pricelist()
			pricelist_context['pricelist'] = pricelist.id
		else:
			pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

		return pricelist_context, pricelist

	def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
		domains = [request.website.sale_product_domain()]
		if search:
			for srch in search.split(" "):
				subdomains = [
					[('name', 'ilike', srch)],
					[('product_variant_ids.default_code', 'ilike', srch)]
				]
				if search_in_description:
					subdomains.append([('description', 'ilike', srch)])
					subdomains.append([('description_sale', 'ilike', srch)])
				domains.append(expression.OR(subdomains))

		if category:
			domains.append([('public_categ_ids', 'child_of', int(category))])

		if attrib_values:
			attrib = None
			ids = []
			for value in attrib_values:
				if not attrib:
					attrib = value[0]
					ids.append(value[1])
				elif value[0] == attrib:
					ids.append(value[1])
				else:
					domains.append([('attribute_line_ids.value_ids', 'in', ids)])
					attrib = value[0]
					ids = [value[1]]
			if attrib:
				domains.append([('attribute_line_ids.value_ids', 'in', ids)])

		return expression.AND(domains)

	def _get_search_order(self, post):
		# OrderBy will be parsed in orm and so no direct sql injection
		# id is added to be sure that order is a unique sort key
		order = post.get('order') or 'website_sequence ASC'
		return 'is_published desc, %s, id desc' % order

	def _get_search_brand_domain(self, search, brand_id):

		domain = request.website.sale_product_domain()
		if search:
			for srch in search.split(" "):
				domain += [
					'|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
					('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

		if brand_id:
			domain += [('brands','=', int(brand_id))]

		return domain
	@http.route([
		'''/shop''',
		'''/shop/page/<int:page>''',
		'''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
		'''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>''',
		'''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand_id>''',
		'''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand_id>/page/<int:page>'''
	], type='http', auth="public", website=True)
	def shop(self, page=0, category=None, search='', ppg=False, brand_id=None, **post):
		add_qty = int(post.get('add_qty', 1))
		Category = request.env['product.public.category']
		if category:
			category = Category.search([('id', '=', int(category))], limit=1)
			if not category or not category.can_access_from_current_website():
				raise NotFound()
		else:
			category = Category

		if brand_id:
			brand_id = request.env['product.brand'].search([('id', '=', int(brand_id))], limit=1)
			if not brand_id:
				raise NotFound()

		if ppg:
			try:
				ppg = int(ppg)
				post['ppg'] = ppg
			except ValueError:
				ppg = False
		if not ppg:
			ppg = request.env['website'].get_current_website().shop_ppg or 20

		ppr = request.env['website'].get_current_website().shop_ppr or 4

		attrib_list = request.httprequest.args.getlist('attrib')
		attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
		attributes_ids = {v[0] for v in attrib_values}
		attrib_set = {v[1] for v in attrib_values}

		domain = self._get_search_domain(search, category, attrib_values)

		domain_brand = self._get_search_brand_domain(search, brand_id)

		keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

		keep_brand = QueryURL('/shop', brand_id=brand_id and int(brand_id), search=search, order=post.get('order'))

		pricelist_context, pricelist = self._get_pricelist_context()

		request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

		url = "/shop"

		if search:
			post["search"] = search
		if attrib_list:
			post['attrib'] = attrib_list

		Product = request.env['product.template'].with_context(bin_size=True)

		search_product = Product.search(domain)
		website_domain = request.website.website_domain()
		categs_domain = [('parent_id', '=', False)] + website_domain
		search_brand = Product.search(domain_brand)
		if search:
			search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
			categs_domain.append(('id', 'in', search_categories.ids))
		else:
			search_categories = Category
		categs = Category.search(categs_domain)

		parent_category_ids = []
		if category:
			url = "/shop/category/%s" % slug(category)
			parent_category_ids = [category.id]
			current_category = category
			while current_category.parent_id:
				parent_category_ids.append(current_category.parent_id.id)
				current_category = current_category.parent_id

		parent_brand_ids = []
		if brand_id:
			url = "/shop/brand/%s" % slug(brand_id)
			parent_brand_ids = [brand_id.id]
			current_brand = brand_id

		product_count = len(search_product)
		brand_count = len(search_brand)

		pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
		
		if brand_id:		
			pager = request.website.pager(url=url, total=brand_count, page=page, step=ppg, scope=7, url_args=post)

		products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))
		
		if brand_id:
			products = Product.search(domain_brand, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))
			
		ProductAttribute = request.env['product.attribute']
		
		if products:
			attributes = ProductAttribute.search([('attribute_line_ids.value_ids', '!=', False), ('attribute_line_ids.product_tmpl_id', 'in', search_product.ids)])        
		else:
			attributes = ProductAttribute.browse(attributes_ids)

		layout_mode = request.session.get('website_sale_shop_layout_mode')
		if not layout_mode:
			if request.website.viewref('website_sale.products_list_view').active:
				layout_mode = 'list'
			else:
				layout_mode = 'grid'

		brands = request.env['product.brand'].search([])

		product_public = request.env['product.template'].search([])

		product_categ = request.env['product.public.category'].search([])

		product_brand = request.env['product.brand'].search([])

		categ_ids = []
		for prod in product_public:
			for ids in prod.public_categ_ids:
				categ_ids.append(ids.id)

		product_count = {i: categ_ids.count(i) for i in categ_ids}

		for ids in product_categ:
			for key, value in product_count.items(): 
				if ids.id == key:
					ids.count = value

		brand_ids = []
		for prod in product_public:
			for ids in prod.brands:
				brand_ids.append(ids.id)

		brand_product_count = {i: brand_ids.count(i) for i in brand_ids}

		for ids in product_brand:
			for key, value in brand_product_count.items(): 
				if ids.id == key:
					ids.count = value
		values = {
			'search': search,
			'category': category,
			'attrib_values': attrib_values,
			'attrib_set': attrib_set,
			'pager': pager,
			'pricelist': pricelist,
			'add_qty': add_qty,
			'products': products,
			'search_count': product_count,  # common for all searchbox
			'bins': TableCompute().process(products, ppg, ppr),
			'ppg': ppg,
			'ppr': ppr,
			'categories': categs,
			'attributes': attributes,
			'keep': keep,
			'search_categories_ids': search_categories.ids,
			'layout_mode': layout_mode,
			'keep_brand':keep_brand,
			'search_brand':search_brand,
			'brand': brands,
			'brand_id': brand_id,
			'parent_brand_ids': parent_brand_ids,
		}
		if category:
			values['main_object'] = category
		return request.render("website_sale.products", values)


class website_brands(http.Controller):

	@http.route('/brands_view', type='http', auth="public", website=True)
	def view_brands(self, brand_id=''):

		brands = request.env['product.brand'].search([])

		keep_brand = QueryURL('/shop', brand_id=brand_id and int(brand_id))

		return request.render("shop_by_filter_app.brand_view_template_id",{'brands':brands, 
																		   'keep_brand':keep_brand,})

	@http.route('''/brand_product_view/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand_id>''', type='http', auth="public", website=True)
	def view_brand_product(self, brand_id='', search=''):

		Product = request.env['product.template'].with_context(bin_size=True)

		products = Product.search([('brands','=',brand_id.id)])

		keep_brand = QueryURL('/shop', brand_id=brand_id and int(brand_id))

		return request.render("shop_by_filter_app.brand_product_view_template",{'products':products,
																				'keep_brand':keep_brand})
