
from datetime import datetime
from openerp.osv import osv, fields
from openerp import models, fields, api


class contrat(models.Model):
    _name = 'cmim.contrat'
    
    import_flag = fields.Boolean('Par import', default=False)      
    name = fields.Char('Nom du contrat')
    for_assure = fields.Boolean("Contrat exceptionnel pour assure", default =False)
    collectivite_id = fields.Many2one('res.partner', string='Collectivite', required=True,  ondelete='cascade')
    assure_id = fields.Many2one('cmim.assure',string='Assure', required=False,  ondelete='cascade') 
    product_id = fields.Many2one('product.template', "Produit")
    
    base_calcul = fields.Selection(
        string='Type du produit',
        related='product_id.base_calcul',
    )
    tarif_id = fields.Many2one('cmim.tarif',  string='Tarif')
    tarif_inc_deces_id = fields.Many2one('cmim.tarif',  string='Tarif Inc_Deces')
    tarif_inv_id = fields.Many2one('cmim.tarif',  string ='Tarif Inv')
   
    @api.onchange('for_assure','assure_id')
    def onchange_assure(self):
        #self.collectivite_id =  assure_id.collectivite_id
        if(self.for_assure and self.assure_id):
            self.collectivite_id =  self.assure_id.collectivite_id
            return {'domain': {'assure_id': []}}
        """if (not self.for_assure):
            return {'invisible': {'assure_id': 1}}
        if (self.collectivite_id and not self.for_assure):
            return {'domain': {'assure_id': [('collectivite_id.id', '=', self.collectivite_id.id)]}}"""
        
    def calcul_cotisation(self):
        return True 
    
class tarif(models.Model):
    _name='cmim.tarif'
    name = fields.Char('Description', required = True)
    type = fields.Selection(selection= [('p', 'Taux'),
                                        ('f', 'Forfait')],
                                        required=True,
                                        default = "p",
                                        string='Type de tarif')
    montant = fields.Float('Tarif')    
    import_flag = fields.Boolean('Par import', default=False)      
    
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
    
    
    
    
    
    