
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api

class constante_calcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)



class cotisation(models.Model):
    _inherit = 'account.invoice'
    _description = 'Import inherit'
    import_flag = fields.Boolean('Par import', default=False)          
    
    
    
class reglement(models.Model):
    _inherit = 'account.payment'
    _default = { 'payment_type' : 'inbound',
                'partner_type': 'customer',
                }
    import_flag = fields.Boolean('Par import', default=False)
    
    
    
class declaration(models.Model):
    _name = 'cmim.declaration'
    
    def _getsalaire_mensuel(self):
        return (self.salaire/self.nb_jour)*30
    
    import_flag = fields.Boolean('Par import', default=False)      
    assure_id =  fields.Many2one('cmim.assure', 'Assure', ondelete='cascade')#domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    collectivite_id = fields.Many2one('res.partner', 'Collectivite', ondelete='cascade')
    nb_jour = fields.Integer('Nombre de jours declares')
    salaire = fields.Float('salaire')
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    #salaire_mensuel = fields.function(_getsalaire_mensuel, string='salaire mensuel', type='Float')
    
    
    
class detail_cotisation(models.Model):    
    _name = 'cmim.detail.cotisation'
    
    collectivite_id = fields.Many2one('res.partner', 'Collectivite')
    assure_id =  fields.Many2one('cmim.assure', 'Assure')#domain=[('collectivite_id.id','=',collectivite_id.id)] , 
    product_id = fields.Many2one('product.template', 'Produit CMIM')
    montant = fields.Float('Montant de la cotisation', default = 0.0)
    
    
    
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    operation = fields.Selection(selection = [('calcul', 'Processus calcul Cotisation'),
                                              ('save','Sauver les cotisations')], 
                                required = True, default = 'calcul')
    def calcul_engine(self):
        return True
    
    def create_entities(self):
        return True
    