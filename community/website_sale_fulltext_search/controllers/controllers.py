# -*- coding: utf-8 -*-

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from odoo.addons.fulltext_search_base.models import fts_base


class WebsiteSaleFullText(WebsiteSale):

    def _get_tsvector_column(self):
        return fts_base.TSVECTOR_COLUMN

    def _get_search_domain(self, search, category, attrib_values, search_in_description=None):
        """ Override to use fulltext search """
        if search_in_description is not None:
            # this search is triggered from autocomplete
            return super(WebsiteSaleFullText, self)._get_search_domain(search, category, attrib_values, search_in_description)

        domain = request.website.sale_product_domain()
        if search:
            domain += [
                (self._get_tsvector_column(), '@@', search)
            ]
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
            
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
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

