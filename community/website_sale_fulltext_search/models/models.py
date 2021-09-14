from odoo.addons.fulltext_search_base.models import fts_base

class FtsProduct(fts_base.FtsModel):   
    _inherit = 'product.template'
    _register = True            # visible in ORM registry
    _abstract = False           # whether model is abstract
    _index_config_id = 'website_sale_fulltext_search.fts_product_index'
    # _indexed_column = ['name', 'description', 'description_sale']

    def _add_orderby_tsrank(self, order):
        temp = order.split(',')
        if len(temp) >= 3:
            if temp[1].strip().startswith('website_sequence'):
                # if only sort with is_published desc,website_sequence asc , id desc
                # replace website_sequence with ts_rank
                temp[1] = fts_base.TSRANK_FIELD + ' DESC'
                return ','.join(temp)
            elif temp[2].strip().startswith('id'):
                # if sort with name intentionally e.g is_published desc,name asc , id desc
                # replace id with tsrank
                temp[2] = fts_base.TSRANK_FIELD + ' DESC'
                return ','.join(temp)
            
        return super(FtsProduct, self)._add_orderby_tsrank(order)