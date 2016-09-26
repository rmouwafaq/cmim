
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api


###################################################################################################

class adherence(models.Model):
    _name = 'cmim.adherence'
    name = fields.Char('Nom de la relation d\'adherence')
    clollectivite_ids = fields.One2many('cmim.collectivite', 'adherence_id', string='Adherents ')
    product_ids = fields.Many2many('product.template', 'collectivite_product_template_rel', 'collectivite_id', 'product_id', "relation d'adherence")
    
    def calcul_cotisation(self):
        return True 
class tarif(models.Model):
    _name='cmim.tarif'
    type = fields.Selection(selection= [('p', 'Taux'),
                                        ('F', 'Forfait')],
                                        required=True,
                                        string='Type')
    tarif = fields.Float('Tarif')
class product_cmim(models.Model):
    _inherit = 'product.template'
    code =  fields.Integer('Code Produit')
    planche = fields.Float('Planche trimestrielle',default="0.0")
    plafond = fields.Float('Plafond trimestrielle')
    tarif = fields.Many2one('cmim.tarif', 'Tarif du produit')
    tarif_incapacite = fields.Float("tarif incapacite deces", default="0.0")
    tarif_invalidite = fields.Float("tarif invalidite deces", default="0.0")
    planche_deces = fields.Float('Planche inv_inc_deces',default="0.0")
    plafond_deces = fields.Float('Plafond inv_inc_deces')
    is_obligatory = fields.Boolean('a un aspect obligatoire', default = False)
    