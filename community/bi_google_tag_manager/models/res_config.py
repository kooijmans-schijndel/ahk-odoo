# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class InheritResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	enable_google_tag_manager = fields.Boolean(string="Enable Google Tag Manager",related="company_id.enable_google_tag_manager",readonly=False)
	gtm_key = fields.Char(string="Container ID",related="company_id.gtm_key",readonly=False)


class InheritResCompany(models.Model):
	_inherit = 'res.company'

	enable_google_tag_manager = fields.Boolean(string="Enable Google Tag Manager")
	gtm_key = fields.Char(string="Container ID")
