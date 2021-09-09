# -*- coding: utf-8 -*-

{
    "name" : "Product Catalog Shop By Brand & Category in Odoo",
    "author": "Edge Technologies",
    "version" : "14.0.1.0",
    "live_test_url":'https://youtu.be/bIxNWdfqLwE',
    "images":['static/description/main_screenshot.png'],
    "summary": 'Website Shop By Filter website Shop By Brand website shop by Category Shop By Brand Shop By Category website sort by Brand website sort by product website sort by category website category filter website brand filter shop search by brand search by category',
    "description": """ This module create your own brand category than select there logo after that in website
					   brand name and product count are show for helps to show how
                        many products in particular brand.


Shop By Filter
Product Catalog Shop By Brand & Category
Shop By Brand & Category
Shop By Category
sort by Brand & Category
sort by product 
sort by category
shop filter
product filter
Website Product Sortby & Shopby
Product Sortby & Shopby
Shop By Product
Website Shop Product Filter in Odoo
Shop Product Filter
Sort products
Show product count
product count
search by brand
search by category
Attribute filters
Category filter





                    """,
    "license" : "OPL-1",
    "depends" : ['base','website_sale','website'],
	'data' : [
		'security/ir.model.access.csv',
		'views/product_brand.xml',
		'views/product_template.xml',
		'views/product_website.xml',
		'views/brands_view.xml',
		'views/brand_product_view.xml',
	],

    "auto_install": False,
    "installable": True,
    "price": 15,
    "currency": 'EUR',
    "category" : "eCommerce",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
