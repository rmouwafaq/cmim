# -*- coding: utf-8 -*-
from openerp import models, fields, api

class ProductCMIM(models.Model):
    _inherit = 'product.template'

    _defaults = {
        'type': 'service',
        }  
    short_name = fields.Char('Intitule Court')
    