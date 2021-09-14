# -*- coding: utf-8 -*-
{
    'name': "Website Ecommerce Full-Text Search",

    'summary': """
        Odoo E-commerce full-text product search""",

    'description': """
        Enable full-text search for products in Odoo E-commerce, which is faster. 
        Indexing is done automatically whenever products are updated. 
        Full-text search by default after install. 
        Search approximately by stemming. 
    """,

    'author': "Beolla Digital",
    'website': "https://beolla.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Ecommerce',
    'version': '14.0.1.0.8',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website_sale', 'fulltext_search_base'],

    # only loaded in demonstration mode
    'application': False,
    'installable': True,
    'license': 'LGPL-3',

    'data': [
        'data/index_config.xml',
        'data/index_cron.xml'
    ],
    'support': 'support@beolla.com',
    'uninstall_hook': 'uninstall_hook',
    'price': 9.99,
    'images': [
        'static/description/banner.png',
        'static/description/config_index_menu.png',
        'static/description/config_index_screenshot.png',
        'static/description/update_index.png'
    ]
}