
from datetime import datetime
from openerp import models, fields, api

    
class product_cmim(models.Model):
    _inherit = 'product.template'

    _defaults = {
        'type': 'service',
        'is_mandatory': False,
        }
    
    import_flag = fields.Boolean('Par import', default=False)      
    code =  fields.Integer('Code Produit')
    is_mandatory = fields.Boolean('a un aspect obligatoire')  
    plancher = fields.Float('Plancher trimestrielle',default="0.0")
    plafond = fields.Float('Plafond trimestrielle')
    base_calcul = fields.Selection(selection= [('tranche', 'Tranche A_B'),
                                        ('salaire', 'Salaire')],
                                        required=True,
                                        string='Base de calcul', 
                                        default = 'salaire')
    
    #contrat_ids = fields.One2many('cmim.contrat','product_id', string="Contrats")
    
    
    
    