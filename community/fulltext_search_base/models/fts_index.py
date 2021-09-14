from odoo import _, api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class FtsIndex(models.Model):
    _description = "Model to store full-text search index config"
    _name = "fts.index"

    name = fields.Char('Name')
    model_name = fields.Char('Model Name')
    cron_name = fields.Char('Cron Name', help='Cron job to trigger re-indexing')
    indexed_columns = fields.One2many(comodel_name='fts.index.column',
        string='Columns to be indexed',
        help='Columns to be searched in',
        inverse_name='index_id'
    )

    indexed_column_str = fields.Char(compute='_compute_idx_col', string='Indexed Columns')

    @api.depends('indexed_columns')
    def _compute_idx_col(self):
        for index in self:
            index.indexed_column_str = ', '.join([x.col_name for x in index.indexed_columns])
        
    def write(self, vals):        
        ori_index_cols = None
        if 'indexed_columns' in vals:
            ori_index_cols = '_'.join(sorted([x.col_name + '_' + x.weight for x in self.indexed_columns]))

        r = super(FtsIndex, self).write(vals)
        if ori_index_cols is not None:
            new_index_cols = '_'.join(sorted([x.col_name + '_' + x.weight for x in self.indexed_columns]))
            if not new_index_cols == ori_index_cols:
                _logger.info('indexed columns changed. Need to reindex')
                self.env.ref(self.cron_name).method_direct_trigger()                        
        return r

class FtsIndexColumn(models.Model):
    _description = "Columns to be indexed"

    _name = "fts.index.column"
    
    def _get_column_names(self, *args):
        """ get column name of a table"""     
        # print('args === ', args, self._context)
        if 'model_name' not in self._context:
            if 'params' in self._context and 'id' in self._context['params']:
                index_id = self._context['params']['id']
                index_obj = self.env['fts.index'].browse(index_id)
                model_name = index_obj.model_name
            else:
                return []
        else:
            model_name = self._context['model_name']

        model_obj = self.env['ir.model'].search([('model', '=', model_name)])        
        fields = self.env['ir.model.fields'].search([('model_id', '=', model_obj.id), ('ttype', 'in', ('selection', 'text', 'char'))])
        r = [(f.name, f.field_description) for f in fields]
        return r

    name = fields.Selection(_get_column_names, string="Name", store=False)
    col_name = fields.Char(string='Column Name')
    index_id = fields.Many2one(comodel_name='fts.index', 
                            string='Fts Index', required=True, index=True, ondelete='cascade',
                            help='Index to which this column belongs')
    weight = fields.Selection([
            ('A', '1.0'),
            ('B', '0.4'),
            ('C', '0.2'),
            ('D', '0.1')
        ], string="Weight", default='A', required=True)

    @api.onchange('name')
    def _onchange_name(self):
        self.col_name = self.name


    def read(self, fields=None, load='_classic_read'):
        if fields and 'col_name' not in fields:
            fields.append('col_name')
        result = super(FtsIndexColumn, self).read(fields=fields, load=load)
        
        for r in result:
            if 'col_name' in r and 'name' in r:
                r['name'] = r['col_name'] if not r['name'] else r['name']
        return result

    def write(self, vals):
        # print('wrting ', vals)
        if 'name' in vals:
            del vals['name']
        return super(FtsIndexColumn, self).write(vals)

    # @api.depends('col_name')
    # def _compute_name(self):
    #     for x in self:
    #         x.name = x.col_name 





