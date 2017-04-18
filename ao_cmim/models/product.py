
from datetime import datetime
from openerp import models, fields, api

class ProductCMIM(models.Model):
    _inherit = 'product.template'

    _defaults = {
        'type': 'service',
        }  
    type_product_ids = fields.Many2many('cmim.product.type', 'pdt_id', 'pdt_type_id', string= "Types des declinaisons")
    short_name = fields.Char('Intitule long')
    