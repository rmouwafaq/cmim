from datetime import datetime
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
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
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

