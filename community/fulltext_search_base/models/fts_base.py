# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import functools
from psycopg2 import sql
import threading

_logger = logging.getLogger(__name__)

IR_ACTION_SERVER_PREFIX = 'Full-text search init'
# TSVECTOR_COLUMN_SUFFIX = '_tsvector'
FTS_LANGUAGE = 'english'
TSRANK_FIELD = 'ts_rank'
TSVECTOR_COLUMN = 'fts_tsvector'
TSVECTOR_COLUMN_TRIGGER = TSVECTOR_COLUMN + '_trigger'

def convert_ts_query(value):
    tokens = value.strip().split(' ')
    if len(tokens[-1]) <= 4 and not value.endswith(' '):
        # make last token prefix matching
        # if word length is less than 3 (assuming that the user has not finished typing)
        tokens[-1] = tokens[-1] + ':*'
    return ' & '.join(tokens)

class FtsDummyField:
    inherited = False
    store = True
    model_name = None
    translate = False
    related_field = None

    def __init__(self, model_name):
        self.model_name = model_name

class FtsTsvectorField(FtsDummyField):
    type = 'tsvector'    
    column_format = "to_tsquery('" + FTS_LANGUAGE + "', %s)"
    column_type = 'tsvector'
    
    comodel_name = None
    prefetch = False

    def convert_to_column(self, value, record, values=None, validate=True):
        """ Convert ``value`` from the ``write`` format to the SQL format. """
        return convert_ts_query(value)

class FtsRankField(FtsDummyField):
    type = 'integer'
    relational = False
    column_type = 'integer'
    prefetch = False



class FtsModel(models.AbstractModel):
    _auto = False               # don't create any database backend
    _register = False           # not visible in ORM registry
    _abstract = True            # whether model is abstract
    _transient = False          # whether model is transient
    
    # _indexed_column = None
    _index_config_id = None
    # _tsvector_column = None
    # _tsvector_column_index = None
    # _tsvector_column_trigger = None
    _tsconfig = FTS_LANGUAGE

    _current_search = threading.local()
    _current_search_count = dict(count=0);
    _field_lock = threading.Lock()

    def get_tsvector_column(self):
        return TSVECTOR_COLUMN

    def get_tsvector_column_index(self):
        return self._table + '.' + self.tsvector_column + '_idx'        

    def get_tsvector_column_trigger(self):
        return TSVECTOR_COLUMN_TRIGGER

    tsvector_column = property(get_tsvector_column)
    tsvector_column_index = property(get_tsvector_column_index)
    tsvector_column_trigger = property(get_tsvector_column_trigger)


    def _create_tsvector_column(self):
        """Create the column to hold tsvector data."""

        if self._name is None or self.tsvector_column is None or\
                self._column_exists(self._table, self.tsvector_column):
            _logger.info('%s already exists on table %s', self.tsvector_column, self._table)
            return False

        self._cr.execute(
            sql.SQL('ALTER TABLE {table} ADD COLUMN {column} tsvector').format(
                    table=sql.Identifier(self._table),
                    column=sql.Identifier(self.tsvector_column)
                )
        )
        _logger.info('created %s on table %s', self.tsvector_column, self._table)     
        return True   


    def _create_tsvector_column_index(self):
        """Create an index on _tsvector_column."""
        self._cr.execute(
            sql.SQL('CREATE INDEX {tsvector_column_index} ON {table} USING gin({tsvector_column})').format(            
                tsvector_column_index=sql.Identifier(self.tsvector_column_index),
                tsvector_column=sql.Identifier(self.tsvector_column),
                table=sql.Identifier(self._table)
            )
        )
        _logger.info('created index %s', self.tsvector_column_index)


    def _get_indexed_columns(self):
        index_config = self.env.ref(self._index_config_id)
        return [(c.col_name, c.weight) for c in index_config.indexed_columns]


    def _create_indexed_column_trigger(self):
        """Create a trigger for changes to _indexed_column"""
        indexed_columns = self._get_indexed_columns()
        if not indexed_columns or len(indexed_columns) == 0:
            _logger.warn('No columns to be indexed. Skip create index trigger')
            return 

        self._cr.execute(
            sql.SQL('''CREATE TRIGGER {tsvector_column_trigger} BEFORE INSERT OR
                                                                        UPDATE
            ON {table} FOR EACH ROW EXECUTE PROCEDURE
            tsvector_update_trigger({tsvector_column}, %s,
            {indexed_column})''').format(
            
                tsvector_column=sql.Identifier(self.tsvector_column),
                tsvector_column_trigger=sql.Identifier(self.tsvector_column_trigger),
                table=sql.Identifier(self._table),                
                indexed_column=(sql.SQL(',').join([sql.Identifier(x) for x, _ in indexed_columns]))
            ),
            ['pg_catalog.' + self._tsconfig]
        )        
        _logger.info('created trigger %s', self.tsvector_column_trigger)


    def fill_tsvector_column(self):
        """Fill _tsvector_column. This can take a long time and is called in a
        cronjob.
        trigger on tsvector_column must be created after updating. Otherwise it causes 
        error `text search configuration name “english” must be schema-qualified`
        """    
        indexed_columns = self._get_indexed_columns()
        if not indexed_columns or len(indexed_columns) == 0:
            _logger.warn('No columns to be indexed. Skip fill tsvector column')
            return

        if self._create_tsvector_column():
            self._create_tsvector_column_index()
            
        self._drop_indexed_column_trigger()            

        _logger.info('start filling data to column %s', self.tsvector_column)        

    
        indexed_column = sql.SQL(" || ").join(
            [sql.SQL('setweight(to_tsvector({lang}, coalesce({field}, {empty})), {weight})').format(
                field=sql.Identifier(name),
                empty=sql.Literal(''),
                weight=sql.Literal(weight),
                lang=sql.Literal(self._tsconfig)
            ) for name, weight in indexed_columns])

        self._cr.execute(
            sql.SQL('''UPDATE {table} SET {tsvector_column}={to_tsvector}''').format(            
                tsvector_column=sql.Identifier(self.tsvector_column),
                table=sql.Identifier(self._table),                
                to_tsvector=indexed_column,
            )
        )
        _logger.info('done indexing %s', self.tsvector_column)

        # create trigger after indexing is done
        self._create_indexed_column_trigger()


    def _drop_indexed_column_trigger(self):
        """Drop the trigger for changes to _indexed_column"""
        self._cr.execute(
            sql.SQL('DROP TRIGGER IF EXISTS {tsvector_column_trigger} ON {table}').format(            
                tsvector_column_trigger=sql.Identifier(self.tsvector_column_trigger),
                table=sql.Identifier(self._table),
            ))


    def _create_init_tsvector_server_action(self):

        # fts_classname = (fts_object._model)
        model_obj = self.env['ir.model'].search([('model', '=', self._name)])

        # create server action

        action = self.env['ir.actions.server'].sudo().create(
            {
                'name': IR_ACTION_SERVER_PREFIX + ' ' + self._name,
                'state': 'code',
                'usage': 'ir_actions_server',
                'model_id': model_obj.id,
                'code': '''
                    env["%(model_name)s"].fill_tsvector_column()
                ''' % {
                    'model_name': self._name
                }
            })
        _logger.info('created server actions "Full-text search init %s"', self._name)

        # create cron to run action
        self.env['ir.cron'].sudo().create(            
            {
                'name': IR_ACTION_SERVER_PREFIX + ' ' + self._name,
                'nextcall': datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT),
                'ir_actions_server_id': action.id,
                'interval_type': False,
                'interval_number': False,
            })
        _logger.info('created cron job to run index in background')


    def _column_exists(self, table, column):
        """Check if a columns exists in a table"""

        self._cr.execute(
            sql.SQL("""SELECT column_name
            FROM information_schema.columns
            WHERE table_name={table} and column_name={column}""").format(
            table=sql.Literal(table),
            column=sql.Literal(column))
        )
        return self._cr.rowcount == 1

    def _add_orderby_tsrank(self, order):        
        return ','.join(order.split(',') + [TSRANK_FIELD + ' DESC'])

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):  

        fts = [x for x in args if type(x) == tuple and len(x) >= 3 and x[1] == '@@'] 
        if len(fts) > 0:
            _, _, search_term = fts[0] # assuming there is only one search
            self._current_search.text = search_term
            with self._field_lock:
                if not order:
                    order = TSRANK_FIELD + ' DESC'
                else:                    
                    order = self._add_orderby_tsrank(order)
                self._current_search_count['count'] += 1
                if self.tsvector_column not in self._fields:
                    self._fields[self.tsvector_column] = FtsTsvectorField(self._name)        

                if order.find(TSRANK_FIELD) >= 0 and TSRANK_FIELD not in self._fields:
                    self._fields[TSRANK_FIELD] = FtsRankField(self._name)                    

            r = super(FtsModel, self)._search(args, offset, limit, order, count, access_rights_uid)

            with self._field_lock:
                self._current_search_count['count'] -=1
                if self._current_search_count['count'] == 0:
                    if self.tsvector_column in self._fields:            
                        del self._fields[self.tsvector_column]
                    if TSRANK_FIELD in self._fields:
                        del self._fields[TSRANK_FIELD]                

            self._current_search.text = None            
            return r
        else:
            return super(FtsModel, self)._search(args, offset, limit, order, count, access_rights_uid) 

    @api.model
    def _inherits_join_calc(self, alias, fname, query):
        """override to allow for order by ts_rank"""
        if fname == TSRANK_FIELD:         
            return sql.SQL('ts_rank({tsvector_column}, to_tsquery({language}, {searchstring}))').format(
                        tsvector_column=sql.Identifier(self.tsvector_column),
                        language=sql.Literal(self._tsconfig),
                        searchstring=sql.Literal(convert_ts_query(self._current_search.text))
                    ).as_string(self._cr._obj)
        return super(FtsModel, self)._inherits_join_calc(alias, fname, query)
