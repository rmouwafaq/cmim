
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api


###################################################################################################
class cotisation(models.TransientModel):
    _inherit = 'account.invoice'
    _description = 'Import inherit'
    import_flag = fields.Boolean('Import', default=False)          
                
class account_payment(models.TransientModel):
    _inherit = 'account.payment'
    _description = 'Import inherit'
    import_flag = fields.Boolean('Import', default=False)

class declaration(models.Model):
    _name = 'cmim.declaration'
    
    def _getsalaire_mensuel(self):
        return (self.salaire/self.nb_jour)*30
    
    assure_id =  fields.Many2one('cmim.assure', 'assure')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    #salaire_mensuel = fields.function(_getsalaire_mensuel, string='salaire mensuel', type='Float')