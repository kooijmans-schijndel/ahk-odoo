# -*- coding: utf-8 -*-

from odoo.addons.fulltext_search_base import base_uninstall_hook

from . import models
from . import controllers

def uninstall_hook(cr, registry):
    base_uninstall_hook(cr, registry, 'product.template')