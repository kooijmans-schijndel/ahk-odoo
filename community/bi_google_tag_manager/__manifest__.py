# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
	"name" : "Google Tag Manager in Odoo",
	"version" : "14.0.0.0",
	"category" : "Website",
	'summary': 'Google Tag Manager google manage all tags google manage tag website google tracking on website visitors tracking google tracking on website google analytics on website google analytics website google tag manager manage google tag Google TMS Tag Analytics',
	"description": """Google Tag Manager Odoo App helps to configure container id in odoo website. 
	User can easily manage all tags without editing code with using google tag manager. 
	User can also add tags for measuring product impressions, product clicks, views of product details, additions to a shopping cart, checkout and purchases.""",
	"author": "BrowseInfo",
	"website" : "https://www.browseinfo.in",
	"price": 25,
	"currency": 'EUR',
	"depends" : ['website'],
	"data": [
		'views/res_config_view.xml',
		'views/template.xml',
	],
	'qweb': [
	],
	"auto_install": False,
	"installable": True,
	"live_test_url":'',
	"images":["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
