
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api

class constante_calcul(models.Model):
    _name = 'cmim.constante'
    name = fields.Char('Nom ', required=True)
    valeur = fields.Char('Valeur ', required=True)



class reglement(models.Model):
    _inherit = 'account.payment'
    _default = { 'payment_type' : 'inbound',
                'partner_type': 'customer',
                }
    import_flag = fields.Boolean('Par import', default=False)
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='partner_id.secteur_id', store=True
    )
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    
    
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
    
class cotisation(models.Model):
    _name = 'cmim.cotisation'
    _description = "Cotisation"
    
    payroll_year_id = fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode de calcul', domain="[('payroll_year_id','=',payroll_year_id)]")
    collectivite_id = fields.Many2one('res.partner', 'Collectivite')
    assure_id = fields.Many2one('cmim.assure', 'Assure')
    name =  fields.Char('Libelle')
    cotisation_line_ids = fields.One2many('cmim.cotisation.line', 'cotisation_id', 'Ligne de calcul')   
    state = fields.Selection(selection=[('draft', 'Brouillon'),
                                        ('valide', 'Validee')],
                                        required=True,
                                        string='Etat', 
                                        default = 'draft')
    montant = fields.Float('Montant Cotisation')

class cotisation_line(models.Model):
    _name = 'cmim.cotisation.line'
    _description = "Lignes ou details du calcul des cotisations"
    _order = 'cotisation_id,sequence'

    cotisation_id = fields.Many2one('cmim.cotisation', 'Cotisation')
    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.template', 'Produit')
    
    code = fields.Integer(
        string='Code Produit',
        related='product_id.code',
        )
    
    base_calcul = fields.Selection(
        string='Type du produit',
        related='product_id.base_calcul',
    )
    
    name = fields.Char('Libelle')
    base= fields.Float('Base de calcul')
    rate1 = fields.Float('Taux 1')
    rate2 = fields.Float('Taux 2')
    montant = fields.Float('Montant') 
    
     
class calcul_cotisation (models.TransientModel):
    _name = 'cmim.calcul.cotisation'
    
    @api.one
    def _get_collectivite_ids(self):
        """cr = self.pool.cursor()
        self.env
        return self.pool.get('sale.order.printorder').search("""
        return self.env['res.partner'].search([])
    payroll_year_id =  fields.Many2one('py.year', 'Calendrier')
    payroll_period_id = fields.Many2one('py.period', 'Periode', domain="[('payroll_year_id','=',payroll_year_id)]")
    collectivite_ids = fields.Many2many('res.partner','calcul_cotisation_collectivite', 'calcul_id', 'partner_id', "Collectivites",default=_get_collectivite_ids)
    
    @api.multi 
    def calcul_engine(self):
        return True
    
   





