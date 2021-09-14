# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID
import logging
from psycopg2 import sql

_logger = logging.getLogger(__name__)

from odoo.osv import expression
if '@@' not in expression.TERM_OPERATORS:
    expression.TERM_OPERATORS = tuple(list(expression.TERM_OPERATORS) + ['@@'])

def base_uninstall_hook(cr, registry, model_name):
    """
    Clean up data after uninstalling
    1. remove ir_action_server and ir_cron created
    2. remove tsvector column, indices and triggers. 
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
    #     model = env['ir.model'].search([('model', '=', model_name)])
        # cr.execute(
        #     sql.SQL("""SELECT column_name
        #     FROM information_schema.columns
        #     WHERE table_name={table} and column_name = {tsvector_column}""").format(
        #         table=sql.Literal(env[model_name]._table), 
        #         tsvector_column=sql.Literal(models.fts_base.TSVECTOR_COLUMN)
        #     )
        # )
            
        # if cr.rowcount == 1:
        # tsvector_column = cr.fetchone()[0]
        cr.execute(sql.SQL("""
            DROP TRIGGER IF EXISTS {column_trigger} ON {table}
            """).format(
                table=sql.Identifier(env[model_name]._table),
                column_trigger=sql.Identifier(models.fts_base.TSVECTOR_COLUMN_TRIGGER)
            ))
        
        cr.execute(sql.SQL("""
            ALTER TABLE {table} DROP COLUMN IF EXISTS {col} 
            """).format(
                table=sql.Identifier(env[model_name]._table), 
                col=sql.Identifier(models.fts_base.TSVECTOR_COLUMN))
        )

