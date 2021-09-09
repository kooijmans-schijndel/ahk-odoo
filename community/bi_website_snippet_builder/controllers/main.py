import odoo
from odoo import http
from odoo.http import request
from datetime import datetime

class SnippetBuilder(http.Controller):

    @http.route('/make/snippet', type='json', auth="user")
    def make_new_snippet(self, name=False, html_code=False, css_code=False, js_code=False, **kw):
        snippet_name = name
        if snippet_name:
            snippet_builder = request.env['website.snippet.builder']
            snippet_builder_rec = snippet_builder.create({
                'name': name,
                'snippet_html': html_code or False,
                'snippet_css': css_code or False,
                'snippet_js': js_code or False,
            })

            now = datetime.now()
            crr_time = now.strftime("%d_%m_%y_%H_%M_%S")
            new_snippet_name = name.replace(" ", "_")
            new_snippet_name += '_'+crr_time

            # Set snippet list view no update True, aviod to remove custom snippet on upgrade module
            snippet_panel_list = request.env['ir.model.data'].search([('name', '=', 'snippet_panel_list')], limit=1)
            snippet_panel_list.noupdate = True

            view = request.env['ir.ui.view']
            new_snippet_arch = """
            <section style="width:100%;">
                <t t-set="snippet_id" t-value='"""+str(snippet_builder_rec.id)+"""' />
                <t t-if="snippet_id" t-set="snippet_record" t-value="request.env['website.snippet.builder'].search([('id','=',snippet_id)])"></t>
                <t t-if="snippet_record and snippet_record.snippet_html">
                    <div t-field="snippet_record.snippet_html"></div>
                </t>
                <t t-if="snippet_record and snippet_record.snippet_css">
                    <style>
                        <t t-raw="snippet_record.snippet_css"></t>
                    </style>
                </t>
                <t t-if="snippet_record and snippet_record.snippet_js">
                    <script type="text/javascript">
                        (function () {
                            <t t-raw="snippet_record.snippet_js"></t>
                        });
                    </script>
                </t>
            </section>
            """

            snippet_view = view.sudo().create({
                'name': name,
                'type' : 'qweb',
                'arch_base': new_snippet_arch,
                'key' : 'bi_website_snippet_builder.'+new_snippet_name,
            })
            snippet_view.xml_id = new_snippet_name

            model_data = request.env['ir.model.data'].sudo().create({
                'module': 'bi_website_snippet_builder',
                'name': new_snippet_name,
                'model': 'ir.ui.view',
                'res_id': snippet_view.id,
            })
            snippet_builder_rec.sudo().write({'view_id': snippet_view})

            # add new snippet to list
            panel_body = request.env['ir.ui.view'].search([('key', '=', 'bi_website_snippet_builder.snippet_panel_list')], limit=1)
            panel_body_arch = panel_body.arch_base
            new_panel = '<t t-snippet="bi_website_snippet_builder.snippet_builder" t-thumbnail="/bi_website_snippet_builder/static/src/img/snippet_builder.png"/> <t t-snippet="bi_website_snippet_builder.'+new_snippet_name+'" t-thumbnail="/bi_website_snippet_builder/static/src/img/snippet_builder.png"/>'
            update_arch = panel_body_arch.replace('<t t-snippet="bi_website_snippet_builder.snippet_builder" t-thumbnail="/bi_website_snippet_builder/static/src/img/snippet_builder.png"/>',new_panel)
            panel_body.sudo().write({'arch_base': update_arch})

            # Set newely created view no update True, aviod to remove custom snippet on upgrade module
            new_model_data = request.env['ir.model.data'].search([('id', '=', model_data.id)])
            new_model_data.noupdate = True

            values = {
                'snippet_id' :snippet_builder_rec.id,
            }
            response = http.Response(template="bi_website_snippet_builder.snippet_demo_view",qcontext=values)
            return response.render()
        return False
