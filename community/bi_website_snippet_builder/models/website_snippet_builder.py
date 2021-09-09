from odoo import api, models, fields
from odoo.http import request

class websiteSnippetBuilder(models.Model):
    _name = 'website.snippet.builder'

    name = fields.Char(string='Snippet Name')
    view_id = fields.Many2one('ir.ui.view', string='View')
    snippet_html = fields.Html("HTML", sanitize_attributes=False, translate=True)
    snippet_css = fields.Text("CSS", sanitize_attributes=False, translate=True)
    snippet_js = fields.Text("JS", sanitize_attributes=False, translate=True)

    def unlink(self):
        snippet_panel_list = request.env['ir.ui.view'].sudo().search([('key', '=', 'bi_website_snippet_builder.snippet_panel_list')], limit=1)
        if snippet_panel_list:
            for rec in self:
                panel_body_arch = snippet_panel_list.arch_base
                update_arch = panel_body_arch.replace('<t t-snippet="'+rec.view_id.key+'" t-thumbnail="/bi_website_snippet_builder/static/src/img/snippet_builder.png"/>', '')
                snippet_panel_list.sudo().write({'arch_base': update_arch})
        return super(websiteSnippetBuilder, self).unlink()