# -*- coding: utf-8 -*-
{
    'name': "Full Text Search Base",

    'summary': """
        Base module for full text (fulltext) search implementation""",

    'description': """
        Base module for full text (fulltext) search implementation. 
    """,

    'author': "Beolla Digital",
    'website': "https://beolla.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '14.0.1.0.8',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml'
    ],

    # only loaded in demonstration mode
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
    'price': 9.99,
    # 'qweb': [
    #     'static/src/xml/exam.xml'
    # ]
    'support': 'support@beolla.com',
    'images': [
        'static/description/banner.png'
    ]
}