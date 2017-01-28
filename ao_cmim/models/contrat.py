from datetime import datetime
from openerp import models, fields, api
    
class contrat(models.Model):
    _name = 'cmim.contrat'
    
    import_flag = fields.Boolean('Par import', default=False)      
    name = fields.Char('Nom du contrat')
    collectivite_id = fields.Many2one('res.partner', string='Collectivite', required=True,  ondelete='cascade')
    product_id = fields.Many2one('product.template', "Produit", required=True)
    code = fields.Integer("Code Produit")
    type_product_id = fields.Many2one("cmim.product.type", string='Type de produit', )
    type_product_name= fields.Char(string="Type de produit" ,related='type_product_id.short_name', store=True)
    
    secteur_id = fields.Many2one('cmim.secteur',
        string='Secteur',
        related='collectivite_id.secteur_id', store=True
    )
    tarif_id = fields.Many2one('cmim.tarif',  string='Tarif')
    tarif_inc_deces_id = fields.Many2one('cmim.tarif',  string='Tarif Inc_Deces')
    tarif_inv_id = fields.Many2one('cmim.tarif',  string ='Tarif Inv')

        
    def calcul_cotisation(self):
        return True 

